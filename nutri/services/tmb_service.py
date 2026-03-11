from nutri.services.common import parse_int_or_zero


class TmbValidationError(ValueError):
    pass


def validate_basic_tmb_fields(post_data):
    peso_raw = str(post_data.get("peso") or "").strip()
    altura_raw = str(post_data.get("height") or "").strip()
    idade_raw = str(post_data.get("age") or "").strip()
    sexo = post_data.get("opcao")

    if sexo not in ["Masculino", "Feminino"]:
        raise TmbValidationError("Selecione o sexo para calcular a dieta.")

    if peso_raw == "" or altura_raw == "" or idade_raw == "":
        raise TmbValidationError("Preencha peso, altura e idade.")

    if "," in altura_raw or "." in altura_raw:
        raise TmbValidationError("Altura deve ser numero inteiro sem virgula. Exemplo: 169")

    if not peso_raw.isdigit() or not altura_raw.isdigit() or not idade_raw.isdigit():
        raise TmbValidationError("Caracteres invalidos")

    peso = int(peso_raw)
    altura = int(altura_raw)
    idade = int(idade_raw)

    if altura > 272 or peso > 300 or idade > 100 or altura <= 0 or peso <= 0 or idade <= 0:
        raise TmbValidationError("Campo(s) invalido(s).")

    return {
        "peso": peso,
        "altura": altura,
        "idade": idade,
        "sexo": sexo,
    }


def parse_calculated_diet_values(raw_value):
    dados_dieta_raw = str(raw_value or "").strip()
    if dados_dieta_raw == "":
        raise TmbValidationError("Clique em Gerar taxa metabolica basal antes de salvar.")

    dados_dieta = [parse_int_or_zero(valor) for valor in dados_dieta_raw.split(",")]
    if len(dados_dieta) < 6 or dados_dieta[0] <= 0 or dados_dieta[1] <= 0 or dados_dieta[2] <= 0:
        raise TmbValidationError("Nao foi possivel validar os dados calculados. Gere novamente.")

    return dados_dieta

