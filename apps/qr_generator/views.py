import io
import base64
import qrcode
import qrcode.image.svg
from qrcode.image.styledimage import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    RoundedModuleDrawer,
    CircleModuleDrawer,
    SquareModuleDrawer,
)
from PIL import Image
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from .models import QRCode, QRScan


# ─── Допоміжна функція генерації QR ──────────────────────
def generate_qr_image(content, fg_color='#000000', bg_color='#FFFFFF',
                      style='square', logo=None, size=300):
    """
    Генерує QR код і повертає PNG як байти.
    """
    # Вибір стилю модулів
    drawer_map = {
        'rounded': RoundedModuleDrawer(),
        'dots': CircleModuleDrawer(),
        'square': SquareModuleDrawer(),
    }
    module_drawer = drawer_map.get(style, SquareModuleDrawer())

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # H для логотипу
        box_size=10,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=module_drawer,
        color_mask=None,
    ).convert('RGBA')

    # Застосовуємо кольори
    if fg_color != '#000000' or bg_color != '#FFFFFF':
        data = img.getdata()
        new_data = []
        fg = tuple(int(fg_color[i:i+2], 16) for i in (1, 3, 5)) + (255,)
        bg = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5)) + (255,)
        for item in data:
            if item[0] < 128:
                new_data.append(fg)
            else:
                new_data.append(bg)
        img.putdata(new_data)

    # Додаємо логотип якщо є
    if logo:
        try:
            logo_img = Image.open(logo).convert('RGBA')
            qr_width, qr_height = img.size
            logo_size = qr_width // 4
            logo_img = logo_img.resize(
                (logo_size, logo_size),
                Image.LANCZOS
            )
            logo_pos = (
                (qr_width - logo_size) // 2,
                (qr_height - logo_size) // 2,
            )
            img.paste(logo_img, logo_pos, logo_img)
        except Exception:
            pass  # Якщо помилка з логотипом — генеруємо без нього

    # Масштабуємо до потрібного розміру
    img = img.resize((size, size), Image.LANCZOS)

    # Конвертуємо в байти
    buffer = io.BytesIO()
    img.convert('RGB').save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    return buffer.getvalue()


# ─── Головна сторінка генератора ─────────────────────────
def generator_view(request):
    qr_image_b64 = None
    qr_obj = None

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        qr_type = request.POST.get('qr_type', 'url')

        if not content:
            messages.error(request, _('Введіть вміст для QR коду'))
            return render(request, 'qr_generator/generator.html')

        # Перевіряємо чи преміум функції доступні
        is_premium = (
            request.user.is_authenticated and
            request.user.is_premium
        )
        is_admin = (
            request.user.is_authenticated and
            request.user.is_admin
        )
        has_premium_access = is_premium or is_admin

        # Параметри дизайну
        fg_color = '#000000'
        bg_color = '#FFFFFF'
        style = 'square'
        logo = None
        is_dynamic = False

        if has_premium_access:
            fg_color = request.POST.get('fg_color', '#000000')
            bg_color = request.POST.get('bg_color', '#FFFFFF')
            style = request.POST.get('style', 'square')
            logo = request.FILES.get('logo')
            is_dynamic = request.POST.get('is_dynamic') == 'on'

        # Генеруємо зображення
        try:
            qr_bytes = generate_qr_image(
                content=content,
                fg_color=fg_color,
                bg_color=bg_color,
                style=style,
                logo=logo,
            )
            qr_image_b64 = base64.b64encode(qr_bytes).decode('utf-8')
        except Exception as e:
            messages.error(request, _('Помилка генерації QR коду'))
            return render(request, 'qr_generator/generator.html')

        # Зберігаємо в базу якщо авторизований
        if request.user.is_authenticated:
            qr_obj = QRCode.objects.create(
                user=request.user,
                qr_type=qr_type,
                content=content,
                is_dynamic=is_dynamic,
                dynamic_url=content if is_dynamic else None,
                fg_color=fg_color,
                bg_color=bg_color,
                style=style,
                title=request.POST.get('title', ''),
                logo=logo,
            )

    return render(request, 'qr_generator/generator.html', {
        'qr_image_b64': qr_image_b64,
        'qr_obj': qr_obj,
        'has_premium_access': (
            request.user.is_authenticated and
            (request.user.is_premium or request.user.is_admin)
        ),
    })


# ─── Завантаження PNG ─────────────────────────────────────
def download_qr_view(request, qr_id):
    qr_obj = get_object_or_404(QRCode, id=qr_id, user=request.user)

    qr_bytes = generate_qr_image(
        content=qr_obj.get_qr_content(),
        fg_color=qr_obj.fg_color,
        bg_color=qr_obj.bg_color,
        style=qr_obj.style,
        logo=qr_obj.logo if qr_obj.logo else None,
        size=1000,  # Висока роздільна здатність
    )

    response = HttpResponse(qr_bytes, content_type='image/png')
    response['Content-Disposition'] = (
        f'attachment; filename="owlqr-{qr_obj.uid}.png"'
    )
    return response


# ─── Redirect для динамічного QR ─────────────────────────
def dynamic_redirect_view(request, uid):
    qr_obj = get_object_or_404(QRCode, uid=uid, is_dynamic=True)

    # Перевіряємо чи власник має активну підписку
    if qr_obj.user and not (
        qr_obj.user.is_premium or qr_obj.user.is_admin
    ):
        return render(request, 'qr_generator/expired.html', {
            'qr_obj': qr_obj
        })

    # Записуємо сканування
    QRScan.objects.create(
        qr_code=qr_obj,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )

    # Оновлюємо лічильник
    qr_obj.scan_count += 1
    qr_obj.last_scanned_at = timezone.now()
    qr_obj.save(update_fields=['scan_count', 'last_scanned_at'])

    return redirect(qr_obj.dynamic_url)


# ─── Кабінет — список QR кодів ───────────────────────────
@login_required
def my_qr_codes_view(request):
    qr_codes = QRCode.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'qr_generator/my_qr_codes.html', {
        'qr_codes': qr_codes,
    })


# ─── Видалення QR коду ────────────────────────────────────
@login_required
@require_POST
def delete_qr_view(request, qr_id):
    qr_obj = get_object_or_404(QRCode, id=qr_id, user=request.user)
    qr_obj.delete()
    messages.success(request, _('QR код видалено'))
    return redirect('qr_generator:my_qr_codes')


# ─── Редагування динамічного URL ─────────────────────────
@login_required
def edit_dynamic_url_view(request, qr_id):
    qr_obj = get_object_or_404(
        QRCode, id=qr_id, user=request.user, is_dynamic=True
    )

    if not (request.user.is_premium or request.user.is_admin):
        messages.error(request, _('Ця функція доступна тільки для Pro'))
        return redirect('payments:pricing')

    if request.method == 'POST':
        new_url = request.POST.get('dynamic_url', '').strip()
        if new_url:
            qr_obj.dynamic_url = new_url
            qr_obj.save(update_fields=['dynamic_url', 'updated_at'])
            messages.success(request, _('Посилання оновлено'))
            return redirect('qr_generator:my_qr_codes')
        else:
            messages.error(request, _('Введіть нове посилання'))

    return render(request, 'qr_generator/edit_dynamic.html', {
        'qr_obj': qr_obj
    })
