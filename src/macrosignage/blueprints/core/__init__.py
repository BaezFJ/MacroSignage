from os.path import join
from slugify import slugify

from flask import Blueprint, render_template, redirect, url_for, request

from macrosignage.utils import allowed_file, save_file_to_upload_dir, \
    get_file_extension, delete_file_from_upload_dir, upload_file_to_path

from .models import Display, Slide
from .forms import SlideForm

core = Blueprint('core', __name__, template_folder='templates')


_initialized = False


@core.before_app_request
def ensure_default_displays():
    """
    Ensure default displays exist (runs once on the first request).
    """
    global _initialized
    if _initialized:
        return
    _initialized = True
    d = Display.query.filter_by(name='Default').first()
    if d is None:
        Display.insert_default_displays()


# allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
# upload_path = current_app.config['UPLOAD_PATH']


@core.get('/')
def index():
    """
    Index page.
    """
    default_display = Display.query.filter_by(name='Default').first()
    displays = Display.query.filter_by(active=True).all()
    if default_display:
        return redirect(
            url_for('.display', public_key=default_display.public_key))
    return render_template('core/index.html', title='Home', displays=displays)


@core.get('/display/<public_key>')
def display(public_key):
    """
    Display page.
    """
    _display = Display.query.filter_by(public_key=public_key).first_or_404()
    return render_template('core/display.html', title='Display',
                           display=_display)


@core.get('/display/list')
def display_list():
    """
    Display list page.
    """
    displays = Display.query.all()
    return render_template('core/display_list.html', title='Displays',
                           displays=displays)


@core.get('/display/<string:public_key>/slides')
def display_slides(public_key):
    """
    Display slides page.
    """
    _display = Display.query.filter_by(public_key=public_key).first_or_404()
    _slides = Slide.query.filter_by(display_id=_display.id).all()
    form = SlideForm()
    return render_template('core/display_slides.html', title='Slides',
                           slides=_slides, form=form, display=_display)


@core.post('/display/<string:public_key>/slides')
def display_slides_post(public_key):
    """
    Handle display slides form submission.
    """
    _display = Display.query.filter_by(public_key=public_key).first_or_404()
    form = SlideForm()
    if form.validate_on_submit():
        bg_file = request.files['background']
        fg_file = request.files['foreground']
        slide = Slide(background=bg_file.filename,
                      foreground=fg_file.filename,
                      title=form.title.data, display_id=_display.id,
                      show_logo=form.show_logo.data)
        slide.save()
        if bg_file and allowed_file(bg_file.filename):
            file_ext = get_file_extension(bg_file.filename)
            file_ext = '.' + file_ext
            bg_file.filename = slugify(slide.public_key) + file_ext
            save_file_to_upload_dir(bg_file)
        if fg_file and allowed_file(fg_file.filename):
            file_ext = get_file_extension(fg_file.filename)
            file_ext = '.' + file_ext
            fg_file.filename = slugify(slide.public_key) + file_ext
            save_file_to_upload_dir(fg_file)
        return redirect(url_for('core.display_slides', public_key=public_key))
    return redirect(url_for('core.display_slides', public_key=public_key))


@core.get('/display/<string:public_key>/slides/<int:slide_id>/delete')
def display_slides_delete(public_key, slide_id):
    """
    Delete slide.
    """
    _display = Display.query.filter_by(public_key=public_key).first_or_404()
    slide = Slide.query.filter_by(id=slide_id).first_or_404()
    slide.delete()
    if slide.background:
        delete_file_from_upload_dir(slide.background)
    delete_file_from_upload_dir(slide.foreground)
    return redirect(url_for('core.display_slides', public_key=public_key))


@core.get('/slides')
def slides():
    """
    Slide list page.
    """
    _slides = Slide.query.all()
    return render_template('core/slides.html', title='Slides', slides=_slides)
