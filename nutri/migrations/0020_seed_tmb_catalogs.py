from decimal import Decimal

from django.db import migrations, models
from django.utils.text import slugify


GOAL_SEED = [
    {"label": "Bulking", "slug": "bulking", "ordem": 1},
    {"label": "Cutting", "slug": "cutting", "ordem": 2},
    {"label": "Manter", "slug": "manter", "ordem": 3},
]

ACTIVITY_SEED = [
    {"label": "Levemente Ativo", "slug": "leve", "fator": Decimal("1.30"), "ordem": 1},
    {"label": "Moderadamente Ativo", "slug": "moderado", "fator": Decimal("1.50"), "ordem": 2},
    {"label": "Bastante Ativo", "slug": "intenso", "fator": Decimal("1.80"), "ordem": 3},
]


def _unique_slug(model, base_slug, current_pk=None):
    normalized = slugify(base_slug) or f"item-{current_pk or 'novo'}"
    candidate = normalized
    suffix = 2

    while model.objects.exclude(pk=current_pk).filter(slug=candidate).exists():
        candidate = f"{normalized}-{suffix}"
        suffix += 1

    return candidate


def _normalize_existing_slugs(model, label_field):
    for item in model.objects.order_by("id"):
        base_value = getattr(item, "slug", "") or getattr(item, label_field, "")
        normalized_slug = _unique_slug(model, base_value, current_pk=item.pk)
        if item.slug != normalized_slug:
            item.slug = normalized_slug
            item.save(update_fields=["slug"])


def _seed_goals(apps):
    objetivo_model = apps.get_model("nutri", "Objetivo")
    _normalize_existing_slugs(objetivo_model, "objetivo")
    canonical_ids = set()

    for config in GOAL_SEED:
        objetivo = (
            objetivo_model.objects.filter(slug=config["slug"]).first()
            or objetivo_model.objects.filter(objetivo__iexact=config["label"]).order_by("id").first()
        )

        if objetivo is None:
            objetivo = objetivo_model(objetivo=config["label"])

        objetivo.objetivo = config["label"]
        objetivo.slug = config["slug"]
        objetivo.ordem = config["ordem"]
        objetivo.save()
        canonical_ids.add(objetivo.pk)

    extra_order = 100
    for objetivo in objetivo_model.objects.exclude(pk__in=canonical_ids).order_by("ordem", "objetivo", "id"):
        if objetivo.ordem != extra_order:
            objetivo.ordem = extra_order
            objetivo.save(update_fields=["ordem"])
        extra_order += 1


def _seed_activities(apps):
    atividade_model = apps.get_model("nutri", "NivelAtividade")
    _normalize_existing_slugs(atividade_model, "atividade")
    canonical_ids = set()

    for atividade in atividade_model.objects.order_by("id"):
        if atividade.fator is None or atividade.fator <= 0:
            atividade.fator = Decimal("1.00")
            atividade.save(update_fields=["fator"])

    for config in ACTIVITY_SEED:
        atividade = (
            atividade_model.objects.filter(slug=config["slug"]).first()
            or atividade_model.objects.filter(atividade__iexact=config["label"]).order_by("id").first()
        )

        if atividade is None:
            atividade = atividade_model(atividade=config["label"])

        atividade.atividade = config["label"]
        atividade.slug = config["slug"]
        atividade.fator = config["fator"]
        atividade.ordem = config["ordem"]
        atividade.save()
        canonical_ids.add(atividade.pk)

    extra_order = 100
    for atividade in atividade_model.objects.exclude(pk__in=canonical_ids).order_by("ordem", "atividade", "id"):
        updates = []
        if atividade.ordem != extra_order:
            atividade.ordem = extra_order
            updates.append("ordem")
        if atividade.fator is None or atividade.fator <= 0:
            atividade.fator = Decimal("1.00")
            updates.append("fator")
        if updates:
            atividade.save(update_fields=updates)
        extra_order += 1


def seed_tmb_catalogs(apps, schema_editor):
    del schema_editor
    _seed_goals(apps)
    _seed_activities(apps)


class Migration(migrations.Migration):
    dependencies = [
        ("nutri", "0019_itemrefeicao_item_ref_dieta_ord_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="objetivo",
            name="ordem",
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="objetivo",
            name="slug",
            field=models.SlugField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="nivelatividade",
            name="fator",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name="nivelatividade",
            name="ordem",
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="nivelatividade",
            name="slug",
            field=models.SlugField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.RunPython(seed_tmb_catalogs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="objetivo",
            name="slug",
            field=models.SlugField(max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name="nivelatividade",
            name="fator",
            field=models.DecimalField(decimal_places=2, max_digits=4),
        ),
        migrations.AlterField(
            model_name="nivelatividade",
            name="slug",
            field=models.SlugField(max_length=64, unique=True),
        ),
    ]
