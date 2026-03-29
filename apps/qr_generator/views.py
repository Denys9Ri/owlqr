import io
import base64
import math
import qrcode
from PIL import Image, ImageDraw
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from .models import QRCode, QRScan


# ─── Допоміжна функція генерації QR ──────────────────────
def generate_qr_image(content, fg_color='#000000', bg_color='#FFFFFF',
                      style='square', eye_style='square', frame='none',
                      frame_text='', gradient='none', gradient_color='#000000',
                      logo=None, size=300):

    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    fg_rgb = hex_to_rgb(fg_color)
    bg_rgb = hex_to_rgb(bg_color)
    grad_rgb = hex_to_rgb(gradient_color)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)

    matrix = qr.get_matrix()
    box_size = 10
    border = 4
    cols = len(matrix[0])
    rows = len(matrix)
    width = (cols + border * 2) * box_size
    height = (rows + border * 2) * box_size

    img = Image.new('RGBA', (width, height), bg_rgb + (255,))
    draw = ImageDraw.Draw(img)

    # Позиції очей в координатах матриці
    eye_origins = [
        (0, 0),           # верхній лівий
        (0, cols - 7),    # верхній правий
        (rows - 7, 0),    # нижній лівий
    ]

    def is_eye_module(row, col):
        for er, ec in eye_origins:
            if er <= row <= er + 6 and ec <= col <= ec + 6:
                return True
        return False

    def draw_eye(draw, px, py, eye_style, fg_rgb, bg_rgb):
        """
        px, py — піксельні координати верхнього лівого кута ока
        Око займає 7x7 модулів
        """
        s = box_size
        outer_size = 7 * s
        inner_offset = s
        inner_size = 5 * s
        core_offset = 2 * s
        core_size = 3 * s

        if eye_style == 'square':
            # Зовнішній квадрат
            draw.rectangle([px, py, px + outer_size, py + outer_size],
                           fill=fg_rgb + (255,))
            # Внутрішній білий
            draw.rectangle([px + inner_offset, py + inner_offset,
                            px + inner_offset + inner_size,
                            py + inner_offset + inner_size],
                           fill=bg_rgb + (255,))
            # Ядро
            draw.rectangle([px + core_offset, py + core_offset,
                            px + core_offset + core_size,
                            py + core_offset + core_size],
                           fill=fg_rgb + (255,))

        elif eye_style == 'rounded':
            r = s
            draw.rounded_rectangle([px, py, px + outer_size, py + outer_size],
                                   radius=r, fill=fg_rgb + (255,))
            draw.rounded_rectangle([px + inner_offset, py + inner_offset,
                                   px + inner_offset + inner_size,
                                   py + inner_offset + inner_size],
                                   radius=r // 2, fill=bg_rgb + (255,))
            draw.rounded_rectangle([px + core_offset, py + core_offset,
                                   px + core_offset + core_size,
                                   py + core_offset + core_size],
                                   radius=r // 2, fill=fg_rgb + (255,))

        elif eye_style == 'circle':
            draw.ellipse([px, py, px + outer_size, py + outer_size],
                        fill=fg_rgb + (255,))
            draw.ellipse([px + inner_offset, py + inner_offset,
                         px + inner_offset + inner_size,
                         py + inner_offset + inner_size],
                        fill=bg_rgb + (255,))
            draw.ellipse([px + core_offset + s // 2,
                         py + core_offset + s // 2,
                         px + core_offset + core_size - s // 2,
                         py + core_offset + core_size - s // 2],
                        fill=fg_rgb + (255,))

        elif eye_style == 'drop':
            r = s * 2
            draw.rounded_rectangle([px, py, px + outer_size, py + outer_size],
                                   radius=r, fill=fg_rgb + (255,))
            draw.rounded_rectangle([px + inner_offset, py + inner_offset,
                                   px + inner_offset + inner_size,
                                   py + inner_offset + inner_size],
                                   radius=r // 2, fill=bg_rgb + (255,))
            draw.ellipse([px + core_offset, py + core_offset,
                         px + core_offset + core_size,
                         py + core_offset + core_size],
                        fill=fg_rgb + (255,))

    # ─── Малюємо модулі ───────────────────────────────────
    for row_idx, row in enumerate(matrix):
        for col_idx, val in enumerate(row):
            if not val:
                continue
            if is_eye_module(row_idx, col_idx):
                continue

            x = (col_idx + border) * box_size
            y = (row_idx + border) * box_size

            if gradient == 'linear':
                t = col_idx / max(cols - 1, 1)
                color = tuple(int(fg_rgb[i] + (grad_rgb[i] - fg_rgb[i]) * t)
                             for i in range(3)) + (255,)
            elif gradient == 'radial':
                cx, cy = cols / 2, rows / 2
                dist = ((col_idx - cx)**2 + (row_idx - cy)**2) ** 0.5
                max_dist = (cx**2 + cy**2) ** 0.5
                t = min(dist / max_dist, 1.0)
                color = tuple(int(fg_rgb[i] + (grad_rgb[i] - fg_rgb[i]) * t)
                             for i in range(3)) + (255,)
            else:
                color = fg_rgb + (255,)

            if style == 'dots':
                margin = 1
                draw.ellipse([x + margin, y + margin,
                             x + box_size - margin, y + box_size - margin],
                            fill=color)
            elif style == 'rounded':
                draw.rounded_rectangle([x + 1, y + 1,
                                       x + box_size - 1, y + box_size - 1],
                                      radius=3, fill=color)
            elif style == 'diamonds':
                cx = x + box_size // 2
                cy = y + box_size // 2
                half = box_size // 2 - 1
                draw.polygon([
                    (cx, cy - half), (cx + half, cy),
                    (cx, cy + half), (cx - half, cy),
                ], fill=color)
            elif style == 'stars':
                cx = x + box_size // 2
                cy = y + box_size // 2
                r_outer = box_size // 2 - 1
                r_inner = r_outer // 2
                points = []
                for i in range(10):
                    angle = math.pi / 5 * i - math.pi / 2
                    r = r_outer if i % 2 == 0 else r_inner
                    points.append((cx + r * math.cos(angle),
                                  cy + r * math.sin(angle)))
                draw.polygon(points, fill=color)
            elif style == 'connected':
                draw.rectangle([x, y, x + box_size, y + box_size], fill=color)
            else:
                draw.rectangle([x + 1, y + 1,
                               x + box_size - 1, y + box_size - 1],
                              fill=color)

    # ─── Малюємо очі правильно ────────────────────────────
    for er, ec in eye_origins:
        # Переводимо координати матриці в пікселі з урахуванням border
        px = (ec + border) * box_size
        py = (er + border) * box_size
        draw_eye(draw, px, py, eye_style, fg_rgb, bg_rgb)

    # ─── Логотип ───────────────────────────────────────────
    if logo:
        try:
            logo_img = Image.open(logo).convert('RGBA')
            qr_width, qr_height = img.size
            logo_size = qr_width // 4
            logo_img = logo_img.resize((logo_size, logo_size), Image.LANCZOS)
            padding = 8
            bg_box = Image.new('RGBA',
                              (logo_size + padding * 2, logo_size + padding * 2),
                              (255, 255, 255, 255))
            lx = (qr_width - logo_size) // 2
            ly = (qr_height - logo_size) // 2
            img.paste(bg_box, (lx - padding, ly - padding), bg_box)
            img.paste(logo_img, (lx, ly), logo_img)
        except Exception:
            pass

    # ─── Рамка ────────────────────────────────────────────
    if frame != 'none':
        frame_height = 48
        new_img = Image.new('RGBA', (width, height + frame_height),
                           bg_rgb + (255,))
        new_img.paste(img, (0, 0))
        frame_draw = ImageDraw.Draw(new_img)

        if frame == 'simple':
            frame_draw.rectangle(
                [0, 0, width - 1, height + frame_height - 1],
                outline=fg_rgb + (255,), width=6
            )
        elif frame in ('scan_me', 'scan_me_en'):
            frame_draw.rectangle(
                [0, 0, width - 1, height + frame_height - 1],
                outline=fg_rgb + (255,), width=6
            )
            frame_draw.rectangle(
                [0, height, width, height + frame_height],
                fill=fg_rgb + (255,)
            )
            text = frame_text if frame_text else (
                'Скануй мене' if frame == 'scan_me' else 'Scan Me'
            )
            try:
                from PIL import ImageFont
                font = ImageFont.load_default()
            except Exception:
                font = None
            bbox = frame_draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = (width - tw) // 2
            ty = height + (frame_height - th) // 2
            frame_draw.text((tx, ty), text, fill=bg_rgb + (255,), font=font)

        img = new_img

    # ─── Масштаб ───────────────────────────────────────────
    img = img.resize((size, size), Image.LANCZOS)

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

        is_premium = request.user.is_authenticated and request.user.is_premium
        is_admin = request.user.is_authenticated and request.user.is_admin
        has_premium_access = is_premium or is_admin

        fg_color = '#000000'
        bg_color = '#FFFFFF'
        style = 'square'
        eye_style = 'square'
        frame = 'none'
        frame_text = ''
        gradient = 'none'
        gradient_color = '#000000'
        logo = None
        is_dynamic = False

        if has_premium_access:
            fg_color = request.POST.get('fg_color', '#000000')
            bg_color = request.POST.get('bg_color', '#FFFFFF')
            style = request.POST.get('style', 'square')
            eye_style = request.POST.get('eye_style', 'square')
            frame = request.POST.get('frame', 'none')
            frame_text = request.POST.get('frame_text', '')
            gradient = request.POST.get('gradient', 'none')
            gradient_color = request.POST.get('gradient_color', '#000000')
            logo = request.FILES.get('logo')
            is_dynamic = request.POST.get('is_dynamic') == 'on'

        try:
            qr_bytes = generate_qr_image(
                content=content,
                fg_color=fg_color,
                bg_color=bg_color,
                style=style,
                eye_style=eye_style,
                frame=frame,
                frame_text=frame_text,
                gradient=gradient,
                gradient_color=gradient_color,
                logo=logo,
            )
            qr_image_b64 = base64.b64encode(qr_bytes).decode('utf-8')
        except Exception as e:
            messages.error(request, _('Помилка генерації QR коду'))
            return render(request, 'qr_generator/generator.html')

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
                eye_style=eye_style,
                frame=frame,
                frame_text=frame_text,
                gradient=gradient,
                gradient_color=gradient_color,
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
        eye_style=qr_obj.eye_style,
        frame=qr_obj.frame,
        frame_text=qr_obj.frame_text,
        gradient=qr_obj.gradient,
        gradient_color=qr_obj.gradient_color,
        logo=qr_obj.logo if qr_obj.logo else None,
        size=1000,
    )

    response = HttpResponse(qr_bytes, content_type='image/png')
    response['Content-Disposition'] = (
        f'attachment; filename="owlqr-{qr_obj.uid}.png"'
    )
    return response


# ─── Redirect для динамічного QR ─────────────────────────
def dynamic_redirect_view(request, uid):
    qr_obj = get_object_or_404(QRCode, uid=uid, is_dynamic=True)

    if qr_obj.user and not (qr_obj.user.is_premium or qr_obj.user.is_admin):
        return render(request, 'qr_generator/expired.html', {'qr_obj': qr_obj})

    QRScan.objects.create(
        qr_code=qr_obj,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )

    qr_obj.scan_count += 1
    qr_obj.last_scanned_at = timezone.now()
    qr_obj.save(update_fields=['scan_count', 'last_scanned_at'])

    return redirect(qr_obj.dynamic_url)


# ─── Кабінет ──────────────────────────────────────────────
@login_required
def my_qr_codes_view(request):
    qr_codes = QRCode.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'qr_generator/my_qr_codes.html', {'qr_codes': qr_codes})


# ─── Видалення ────────────────────────────────────────────
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
    qr_obj = get_object_or_404(QRCode, id=qr_id, user=request.user, is_dynamic=True)

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

    return render(request, 'qr_generator/edit_dynamic.html', {'qr_obj': qr_obj})
