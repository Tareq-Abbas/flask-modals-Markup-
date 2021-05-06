from flask import Blueprint, g, render_template, get_flashed_messages
from jinja2 import Markup
from turbo_flask import Turbo

from flask_modals.parser import add_turbo_stream_ids

turbo = Turbo()


def modal_messages():
    '''This will be available in the app templates for use in the modal
    body.
    '''
    return Markup(render_template('modals/modal_messages.html'))


def render_template_modal(*args, **kwargs):
    '''Call this function instead of render_template when the page
    contains a modal form.

    It accepts all the arguments passed to render_template and 2 others:

    modal: id of the modal
    turbo: Set this to False if modal is not be displayed. It should be
           True for initial page loads and for modal display.
    '''

    modal = kwargs.pop('modal', None)
    check_turbo = kwargs.pop('turbo', True)
    g._include = True  # used in extension templates

    if check_turbo:
        if turbo.can_stream():
            # prevent flash messages from showing both outside and
            # inside the modal
            g._modal = True

    html, stream, target = add_turbo_stream_ids(
        render_template(*args, **kwargs),
        modal
    )

    if g.get('_modal'):
        return turbo.stream(turbo.replace(stream, target=target))

    return html


class Modal:
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        '''Initialize the Turbo-Flask extension and register template
        globals for app.
        '''

        self.app = app
        turbo.init_app(app)
        self.register_blueprint(app)
        self.app.add_template_global(modal_messages)
        self.app.jinja_env.globals['modals'] = self.load
        self.app.jinja_env.globals['show_flashed_messages'] = \
            self.show_flashed_messages

    def register_blueprint(self, app):

        bp = Blueprint('modals', __name__, template_folder='templates',
                       static_folder='static',
                       static_url_path='/modals/static')
        app.register_blueprint(bp)

    @staticmethod
    def show_flashed_messages(*args, **kwargs):
        '''Delegate to get_flashed_messages if _modal is set on the
        Flask g object. If it is not set, it means modal is not being
        displayed and so we do not flash messages in it.
        '''

        if not g.get('_modal'):
            return

        return get_flashed_messages(*args, **kwargs)

    def load(self):
        '''Load the following markup only if page has a modal form:

        1. turbo.html - Hotwire Turbo library
        2. nprogress.html - NProgress js library for progress bar
        3. jstemplate.html - Remove extra modal-backdrop divs and
                             control progress bar.
        4. bodyattr.html - Add attribute to body element to disable
                           turbo for pages without modal forms.
                           (always loaded)
        '''

        html = (Markup(render_template('modals/turbo.html') +
                       render_template('modals/nprogress.html') +
                       render_template('modals/jstemplate.html') +
                       render_template('modals/bodyattr.html')))

        return html
