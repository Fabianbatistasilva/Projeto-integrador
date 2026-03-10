import json

import requests
from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework import filters, permissions, viewsets

from nutri.serializers import DietaSerializer, ImprimirDietaSerializer, UserSerializer
from .models import Dieta, ImprimirDieta, ItemRefeicao, NivelAtividade, Objetivo

def extract_taco_results(payload):
    if isinstance(payload, dict):
        results = payload.get('results')
        if isinstance(results, list):
            return results
    if isinstance(payload, list):
        return payload
    return []

def fetch_taco_alimentos(search_text=None):
    base_url = str(getattr(settings, 'TACO_API_BASE_URL', '') or '').strip().rstrip('/')
    if base_url == '':
        return []

    cache_key = f"taco_alimentos::{str(search_text or '').strip().lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = {'ordering': 'name'}
    if search_text:
        params['search'] = search_text

    try:
        response = requests.get(
            f'{base_url}/alimentos/',
            params=params,
            timeout=getattr(settings, 'TACO_API_TIMEOUT', 8),
        )
        response.raise_for_status()
        results = extract_taco_results(response.json())
        cache.set(cache_key, results, timeout=getattr(settings, 'TACO_SEARCH_CACHE_SECONDS', 60))
        return results
    except requests.RequestException:
        return []

def parse_int_or_zero(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

##api dos dados do banco##
class DietaViewSet(viewsets.ModelViewSet):
    queryset = Dieta.objects.all()
    serializer_class = DietaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter,filters.OrderingFilter]
    search_fields  = ['usuario__username', 'genero']
    ordering_fields = ['id', 'usuario__username', 'genero']

    def get_queryset(self):
        queryset = Dieta.objects.select_related('usuario', 'objetivo', 'nivel_atividade')
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter,filters.OrderingFilter]
    search_fields  = ['id','username']
    ordering_fields = ['id','username']

class ImprimirDietaViewSet(viewsets.ModelViewSet):
    queryset = ImprimirDieta.objects.all()
    serializer_class = ImprimirDietaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter,filters.OrderingFilter]
    search_fields  = ['id', 'usuario__username']
    ordering_fields = ['id', 'usuario__username']

    def get_queryset(self):
        queryset = ImprimirDieta.objects.select_related('usuario').prefetch_related('itens')
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


def index(request):
    return render(request,'paginas/home.html')


def _client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return str(forwarded_for).split(',')[0].strip()
    return str(request.META.get('REMOTE_ADDR') or 'unknown').strip()


def _login_throttle_key(request, username):
    normalized_user = str(username or '').strip().lower()
    return f'login_attempt::{_client_ip(request)}::{normalized_user}'


def healthcheck(request):
    db_ok = True
    cache_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception:
        db_ok = False

    try:
        cache_key = 'healthcheck::cache_probe'
        probe_value = timezone.now().isoformat()
        cache.set(cache_key, probe_value, timeout=30)
        cached_value = cache.get(cache_key)
        if cached_value != probe_value:
            cache_ok = False
    except Exception:
        cache_ok = False

    status_code = 200
    if not db_ok:
        status_code = 503
    elif not cache_ok and not settings.DEBUG:
        status_code = 503

    return JsonResponse(
        {
            'status': 'ok' if db_ok and cache_ok else 'degraded',
            'app': 'nutrients',
            'database': 'ok' if db_ok else 'error',
            'cache': 'ok' if cache_ok else 'error',
            'timestamp': timezone.now().isoformat(),
        },
        status=status_code,
    )

def UserLogin(request):
    if request.method == 'POST':
        nome = request.POST.get('username')
        senha = request.POST.get('password')
        throttle_key = _login_throttle_key(request, nome)
        max_attempts = int(getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5))
        block_seconds = int(getattr(settings, 'LOGIN_BLOCK_SECONDS', 300))
        failed_attempts = int(cache.get(throttle_key, 0) or 0)

        if failed_attempts >= max_attempts:
            messages.info(request, 'Muitas tentativas de login. Aguarde alguns minutos e tente novamente.')
            return render(request,'paginas/login.html')

        check = auth.authenticate(request, username=nome, password=senha)
        if check is not None:
            cache.delete(throttle_key)
            login(request, check)
            return redirect('home')
        else:
            cache.set(throttle_key, failed_attempts + 1, timeout=block_seconds)
            messages.info(request, 'Login invalido.')
            return render(request,'paginas/login.html')
    else:
        return render(request,'paginas/login.html')

def UserLogout(request):
    logout(request)
    return redirect('login_site')

def UserRegistration(request):
    if request.method != 'POST':
        return render(request, 'paginas/registration_screen.html')

    nome = str(request.POST.get('username') or '').strip()
    senha = str(request.POST.get('password') or '')
    conf_senha = str(request.POST.get('conf_password') or '')

    if nome == '' or senha == '' or conf_senha == '':
        messages.info(request, 'Preencha todos os campos.')
        return render(request, 'paginas/registration_screen.html')

    if User.objects.filter(username=nome).exists():
        messages.info(request, 'Usuario ja existe.')
        return render(request, 'paginas/registration_screen.html')

    if senha != conf_senha:
        messages.info(request, 'As senhas nao conferem.')
        return render(request, 'paginas/registration_screen.html')

    try:
        validate_password(senha, user=User(username=nome))
    except ValidationError as error:
        for message in error.messages:
            messages.info(request, message)
        return render(request, 'paginas/registration_screen.html')

    User.objects.create_user(username=nome, password=senha)
    return redirect('login_site')

def introducao(request):
    if request.user.is_authenticated:
        has_dieta = Dieta.objects.filter(usuario_id=request.user.id, dieta=True).exists()
        return render(request, 'paginas/introdução_dieta.html', {'veri_dieta': has_dieta})
    return render(request, 'paginas/introdução_dieta.html')


def calcular_refeicao(alimento,quantidade,proteina,gordura,carboidratos,kcal):
    alimentos = str(alimento or '').strip()
    quantidades = parse_int_or_zero(quantidade)
    proteinas = parse_int_or_zero(proteina)
    gorduras = parse_int_or_zero(gordura)
    carboidratos = parse_int_or_zero(carboidratos)
    kcals = parse_int_or_zero(kcal)

    if quantidades <= 0 or alimentos == '':
        return ['', 0, 0, 0, 0, 0]

    proteinas = int((quantidades / 100) * proteinas)
    carboidratos = int((quantidades / 100) * carboidratos)
    gorduras = int((quantidades / 100) * gorduras)
    kcals = int((quantidades / 100) * kcals)
    resultado_macros = [alimentos, quantidades, kcals, proteinas, carboidratos, gorduras]
    return resultado_macros

def _normalize_meal_payload(payload):
    selected_meals = parse_int_or_zero(payload.get('selected_meals'))
    if selected_meals < 2 or selected_meals > 6:
        selected_meals = 6

    meals_payload = payload.get('meals')
    if not isinstance(meals_payload, list):
        meals_payload = []

    normalized = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for meal in meals_payload:
        if not isinstance(meal, dict):
            continue

        refeicao = parse_int_or_zero(meal.get('refeicao'))
        if refeicao < 1 or refeicao > 6:
            continue

        raw_items = meal.get('items')
        if not isinstance(raw_items, list):
            continue

        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue

            alimento = str(raw_item.get('name', '') or '').strip()
            quantidade = parse_int_or_zero(raw_item.get('quantidade'))
            kcal_base = parse_int_or_zero(raw_item.get('kcal_base'))
            prot_base = parse_int_or_zero(raw_item.get('prot_base'))
            gord_base = parse_int_or_zero(raw_item.get('gord_base'))
            carb_base = parse_int_or_zero(raw_item.get('carb_base'))

            if not alimento and quantidade <= 0:
                continue

            if alimento == '' or quantidade <= 0:
                raise ValueError('item_invalido')

            resultado = calcular_refeicao(
                alimento,
                quantidade,
                prot_base,
                gord_base,
                carb_base,
                kcal_base,
            )
            normalized[refeicao].append(
                {
                    'alimento': resultado[0],
                    'quantidade': resultado[1],
                    'kcal': resultado[2],
                    'prot': resultado[3],
                    'carb': resultado[4],
                    'gord': resultado[5],
                }
            )

    return selected_meals, normalized


def _apply_legacy_fields(imprimir_dieta, meal_map):
    for refeicao in range(1, 7):
        for ordem in range(1, 4):
            sufixo = f'{refeicao}{ordem}'
            setattr(imprimir_dieta, f'ref_{sufixo}', '')
            setattr(imprimir_dieta, f'quant_{sufixo}', 0)
            setattr(imprimir_dieta, f'kcal_{sufixo}', 0)
            setattr(imprimir_dieta, f'prot_{sufixo}', 0)
            setattr(imprimir_dieta, f'gord_{sufixo}', 0)
            setattr(imprimir_dieta, f'carb_{sufixo}', 0)

        for ordem, item in enumerate(meal_map.get(refeicao, [])[:3], start=1):
            sufixo = f'{refeicao}{ordem}'
            setattr(imprimir_dieta, f'ref_{sufixo}', item['alimento'])
            setattr(imprimir_dieta, f'quant_{sufixo}', item['quantidade'])
            setattr(imprimir_dieta, f'kcal_{sufixo}', item['kcal'])
            setattr(imprimir_dieta, f'prot_{sufixo}', item['prot'])
            setattr(imprimir_dieta, f'gord_{sufixo}', item['gord'])
            setattr(imprimir_dieta, f'carb_{sufixo}', item['carb'])


@transaction.atomic
def _save_dynamic_diet(user_id, meal_map):
    imprimir_dieta = ImprimirDieta.objects.filter(usuario_id=user_id).first()
    if not imprimir_dieta:
        imprimir_dieta = ImprimirDieta.objects.create(
            usuario_id=user_id,
            ref_11='',
            ref_12='',
            ref_13='',
            ref_21='',
            ref_22='',
            ref_23='',
        )

    imprimir_dieta.itens.all().delete()

    novos_itens = []
    for refeicao in range(1, 7):
        for ordem, item in enumerate(meal_map.get(refeicao, []), start=1):
            novos_itens.append(
                ItemRefeicao(
                    dieta=imprimir_dieta,
                    refeicao=refeicao,
                    ordem=ordem,
                    alimento=item['alimento'],
                    quantidade=item['quantidade'],
                    kcal=item['kcal'],
                    prot=item['prot'],
                    gord=item['gord'],
                    carb=item['carb'],
                )
            )

    if novos_itens:
        ItemRefeicao.objects.bulk_create(novos_itens)

    _apply_legacy_fields(imprimir_dieta, meal_map)
    imprimir_dieta.save()


def _taco_api_url():
    base_url = str(getattr(settings, 'TACO_API_BASE_URL', '') or '').strip().rstrip('/')
    if base_url == '':
        return ''
    return f'{base_url}/alimentos/'


def _taco_api_token():
    return str(getattr(settings, 'TACO_API_TOKEN', '') or '').strip()


def _taco_auth_headers():
    token = _taco_api_token()
    if token == '':
        return {}
    return {'Authorization': f'Token {token}'}


def _is_taco_configured():
    return _taco_api_url() != ''


def _is_taco_write_configured():
    return _is_taco_configured() and _taco_api_token() != ''


def create_diet(request):
    if request.user.is_authenticated is False:
        return redirect('login_site')

    pesquisa = (request.GET.get('txtbuscar') or '').strip()
    taco = fetch_taco_alimentos(pesquisa if pesquisa else None)
    dados = Dieta.objects.filter(usuario_id=request.user.id).first()
    if not dados:
        messages.info(request, 'Preencha os dados de objetivo antes de montar a dieta.')
        return redirect('tela_tmb')

    if request.method == 'POST':
        raw_payload = request.POST.get('diet_payload', '')
        if raw_payload == '':
            messages.info(request, 'Nao foi possivel ler os dados da dieta.')
            return redirect('criar_dieta')

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            messages.info(request, 'Formato da dieta invalido.')
            return redirect('criar_dieta')

        if not isinstance(payload, dict):
            messages.info(request, 'Formato da dieta invalido.')
            return redirect('criar_dieta')

        try:
            selected_meals, meal_map = _normalize_meal_payload(payload)
        except ValueError:
            messages.info(request, 'Revise os alimentos e quantidades antes de salvar.')
            return redirect('criar_dieta')

        total_itens = 0
        for refeicao in range(1, selected_meals + 1):
            total_itens += len(meal_map.get(refeicao, []))

        if total_itens == 0:
            messages.info(request, 'Adicione alimentos para montar sua dieta.')
            return redirect('criar_dieta')

        _save_dynamic_diet(request.user.id, meal_map)
        return redirect('diet_screen')

    return render(request, 'paginas/create_diet.html', {'taco': taco, 'dados': dados, 'taco_configured': _is_taco_configured()})

def taco_search(request):
    if request.user.is_authenticated is False:
        return JsonResponse({'detail': 'authentication_required'}, status=401)
    if request.method != 'GET':
        return JsonResponse({'detail': 'method_not_allowed'}, status=405)
    if not _is_taco_configured():
        return JsonResponse({'detail': 'API TACO nao configurada neste ambiente.'}, status=503)

    search_term = (request.GET.get('search') or '').strip()
    taco = fetch_taco_alimentos(search_term)
    return JsonResponse({'results': taco})

def taco_create(request):
    if request.user.is_authenticated is False:
        return JsonResponse({'detail': 'authentication_required'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'detail': 'method_not_allowed'}, status=405)
    if not _is_taco_configured():
        return JsonResponse({'detail': 'API TACO nao configurada neste ambiente.'}, status=503)
    if not _is_taco_write_configured():
        return JsonResponse({'detail': 'Token da API TACO nao configurado neste ambiente.'}, status=503)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'detail': 'payload_invalido'}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({'detail': 'payload_invalido'}, status=400)

    name = str(payload.get('name') or '').strip()
    if name == '':
        return JsonResponse({'detail': 'Nome do alimento e obrigatorio.'}, status=400)

    parsed_macros = {}
    for field in ['kcal', 'protein', 'fat', 'carbo']:
        raw_value = payload.get(field)
        if raw_value in [None, '']:
            return JsonResponse({'detail': f'Campo {field} e obrigatorio.'}, status=400)
        try:
            parsed_value = int(raw_value)
        except (TypeError, ValueError):
            return JsonResponse({'detail': f'Campo {field} precisa ser inteiro.'}, status=400)
        if parsed_value < 0:
            return JsonResponse({'detail': f'Campo {field} nao pode ser negativo.'}, status=400)
        parsed_macros[field] = parsed_value

    upstream_payload = {
        'name': name,
        'kcal': parsed_macros['kcal'],
        'protein': parsed_macros['protein'],
        'fat': parsed_macros['fat'],
        'carbo': parsed_macros['carbo'],
    }

    upstream_url = _taco_api_url()
    if upstream_url == '':
        return JsonResponse({'detail': 'API TACO nao configurada neste ambiente.'}, status=503)

    try:
        response = requests.post(
            upstream_url,
            json=upstream_payload,
            headers=_taco_auth_headers(),
            timeout=getattr(settings, 'TACO_API_WRITE_TIMEOUT', 10),
        )
    except requests.RequestException:
        return JsonResponse({'detail': 'Falha ao conectar na API TACO.'}, status=502)

    try:
        upstream_response = response.json()
    except ValueError:
        upstream_response = {}

    if response.status_code >= 400:
        detail = 'Falha ao criar alimento na API TACO.'
        if isinstance(upstream_response, dict):
            detail = upstream_response.get('detail') or detail
        return JsonResponse({'detail': detail, 'upstream': upstream_response}, status=response.status_code)

    return JsonResponse(
        {'detail': 'created', 'item': upstream_response},
        status=201 if response.status_code == 201 else 200,
    )

def tela_tmb(request):
    if request.user.is_authenticated is False:
        return redirect('login_site')
    
    objetivos = Objetivo.objects.all()
    niveis_atividade = NivelAtividade.objects.all()
    verUser = Dieta.objects.filter(usuario_id=request.user.id).first()

    if request.method == 'POST':
        peso_raw = str(request.POST.get('peso') or '').strip()
        altura_raw = str(request.POST.get('height') or '').strip()
        idade_raw = str(request.POST.get('age') or '').strip()
        sexo = request.POST.get('opcao')
        objetivo_id = request.POST.get('objetivo_user')
        nivel_atividade_id = request.POST.get('nivel_de_ati_user')
        dados_dieta_raw = str(request.POST.get('local_dados_do_user') or '').strip()

        if sexo not in ['Masculino', 'Feminino']:
            messages.info(request, 'Selecione o sexo para calcular a dieta.')
            return redirect('tela_tmb')

        objetivo_int = parse_int_or_zero(objetivo_id)
        nivel_atividade_int = parse_int_or_zero(nivel_atividade_id)
        if objetivo_int <= 0 or nivel_atividade_int <= 0:
            messages.info(request, 'Selecione objetivo e nivel de atividade.')
            return redirect('tela_tmb')

        if not Objetivo.objects.filter(id=objetivo_int).exists() or not NivelAtividade.objects.filter(id=nivel_atividade_int).exists():
            messages.info(request, 'Objetivo ou nivel de atividade invalido.')
            return redirect('tela_tmb')

        if peso_raw == '' or altura_raw == '' or idade_raw == '':
            messages.info(request, 'Preencha peso, altura e idade.')
            return redirect('tela_tmb')

        if ',' in altura_raw or '.' in altura_raw:
            messages.info(request, 'Altura deve ser numero inteiro sem virgula. Exemplo: 169')
            return redirect('tela_tmb')

        if not peso_raw.isdigit() or not altura_raw.isdigit() or not idade_raw.isdigit():
            messages.info(request, 'Caracteres invalidos')
            return redirect('tela_tmb')

        peso = int(peso_raw)
        altura = int(altura_raw)
        idade = int(idade_raw)

        if altura > 272 or peso > 300 or idade > 100 or altura <= 0 or peso <= 0 or idade <= 0:
            messages.info(request, 'Campo(s) invalido(s).')
            return redirect('tela_tmb')

        if dados_dieta_raw == '':
            messages.info(request, 'Clique em Gerar taxa metabolica basal antes de salvar.')
            return redirect('tela_tmb')

        dados_dieta = [parse_int_or_zero(valor) for valor in dados_dieta_raw.split(',')]
        if len(dados_dieta) < 6 or dados_dieta[0] <= 0 or dados_dieta[1] <= 0 or dados_dieta[2] <= 0:
            messages.info(request, 'Nao foi possivel validar os dados calculados. Gere novamente.')
            return redirect('tela_tmb')

        payload = {
            'objetivo_id': objetivo_int,
            'peso': peso,
            'altura': altura,
            'idade': idade,
            'genero': sexo,
            'tmb': dados_dieta[0],
            'gasto_dia': dados_dieta[1],
            'caloria_dieta': dados_dieta[2],
            'proteina': dados_dieta[3],
            'gordura': dados_dieta[4],
            'carboidratos': dados_dieta[5],
            'nivel_atividade_id': nivel_atividade_int,
            'dieta': True,
        }

        updated = Dieta.objects.filter(usuario_id=request.user.id).update(**payload)
        if updated == 0:
            Dieta.objects.create(usuario_id=request.user.id, **payload)

        return redirect('criar_dieta')

    return render(
        request,
        'paginas/tela_tmb.html',
        {'objetivo': objetivos, 'nivel_at': niveis_atividade, 'verUser': verUser},
    )
    
def _legacy_item_dict(dieta, refeicao, ordem):
    sufixo = f'{refeicao}{ordem}'
    nome = str(getattr(dieta, f'ref_{sufixo}', '') or '').strip()
    quantidade = parse_int_or_zero(getattr(dieta, f'quant_{sufixo}', 0))
    kcal = parse_int_or_zero(getattr(dieta, f'kcal_{sufixo}', 0))
    prot = parse_int_or_zero(getattr(dieta, f'prot_{sufixo}', 0))
    gord = parse_int_or_zero(getattr(dieta, f'gord_{sufixo}', 0))
    carb = parse_int_or_zero(getattr(dieta, f'carb_{sufixo}', 0))

    if nome == '' or quantidade <= 0:
        return None

    return {
        'nome': nome,
        'quantidade': quantidade,
        'kcal': kcal,
        'prot': prot,
        'gord': gord,
        'carb': carb,
    }


def _build_meals_for_screen(dieta):
    meals = []
    total_kcal = 0
    total_prot = 0
    total_carb = 0
    total_gord = 0

    related_items = list(dieta.itens.all().order_by('refeicao', 'ordem', 'id'))
    grouped = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}

    if related_items:
        for item in related_items:
            grouped[item.refeicao].append(
                {
                    'nome': item.alimento,
                    'quantidade': item.quantidade,
                    'kcal': item.kcal,
                    'prot': item.prot,
                    'gord': item.gord,
                    'carb': item.carb,
                }
            )
    else:
        for refeicao in range(1, 7):
            for ordem in range(1, 4):
                legacy_item = _legacy_item_dict(dieta, refeicao, ordem)
                if legacy_item:
                    grouped[refeicao].append(legacy_item)

    for refeicao in range(1, 7):
        itens = grouped[refeicao]
        if not itens:
            continue

        subtotal_kcal = sum(item['kcal'] for item in itens)
        subtotal_qtd = sum(item['quantidade'] for item in itens)
        subtotal_prot = sum(item['prot'] for item in itens)
        subtotal_carb = sum(item['carb'] for item in itens)
        subtotal_gord = sum(item['gord'] for item in itens)

        meals.append(
            {
                'numero': refeicao,
                'itens': itens,
                'subtotal_qtd': subtotal_qtd,
                'subtotal_kcal': subtotal_kcal,
                'subtotal_prot': subtotal_prot,
                'subtotal_carb': subtotal_carb,
                'subtotal_gord': subtotal_gord,
            }
        )

        total_kcal += subtotal_kcal
        total_prot += subtotal_prot
        total_carb += subtotal_carb
        total_gord += subtotal_gord

    return meals, total_kcal, total_prot, total_carb, total_gord


def diet_screen(request):
    if request.user.is_authenticated is False:
        messages.info(request, 'Faca o Login')
        return redirect('login_site')

    dieta = ImprimirDieta.objects.filter(usuario_id=request.user.id).first()
    if not dieta:
        verificar_tmb = Dieta.objects.filter(usuario_id=request.user.id).exists()
        if verificar_tmb:
            messages.info(request, 'Faca as refeicoes')
            return redirect('criar_dieta')
        messages.info(request, 'Preencha os dados')
        return redirect('tela_tmb')

    meals, total_caloria, total_proteina, total_carboidratos, total_gordura = _build_meals_for_screen(dieta)
    total_quantidade = sum(meal.get('subtotal_qtd', 0) for meal in meals)
    perfil_base = (
        Dieta.objects.select_related('objetivo', 'nivel_atividade')
        .filter(usuario_id=request.user.id)
        .first()
    )

    objetivo_nome = ''
    nivel_atividade_nome = ''
    peso_usuario = None
    altura_usuario = None
    idade_usuario = None
    gasto_dia = None

    if perfil_base:
        if perfil_base.objetivo_id:
            objetivo_nome = perfil_base.objetivo.objetivo
        if perfil_base.nivel_atividade_id:
            nivel_atividade_nome = perfil_base.nivel_atividade.atividade
        peso_usuario = perfil_base.peso
        altura_usuario = perfil_base.altura
        idade_usuario = perfil_base.idade
        gasto_dia = perfil_base.gasto_dia

    return render(
        request,
        'paginas/diet_screen.html',
        {
            'meals': meals,
            'total_caloria': total_caloria,
            'total_proteina': total_proteina,
            'total_carboidratos': total_carboidratos,
            'total_gordura': total_gordura,
            'total_quantidade': total_quantidade,
            'objetivo_nome': objetivo_nome,
            'nivel_atividade_nome': nivel_atividade_nome,
            'peso_usuario': peso_usuario,
            'altura_usuario': altura_usuario,
            'idade_usuario': idade_usuario,
            'gasto_dia': gasto_dia,
        },
    )

