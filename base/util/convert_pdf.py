from io import BytesIO

from django.template.loader import get_template
from weasyprint import CSS, HTML
from xhtml2pdf import pisa

from Eggoz import settings


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return result.getvalue()
    return None


def create_pdf(html_file_path, pdf_context, css_file_urls):
    print(settings.BASE_DIR)
    html_template = get_template(html_file_path)
    rendered_html = html_template.render(pdf_context)
    request = pdf_context.get('request')
    return HTML(string=rendered_html, base_url=request.build_absolute_uri()).write_pdf(
        stylesheets=[CSS(settings.BASE_DIR + file_url) for file_url in css_file_urls]
    )


def create_pdf_async(html_file_path, pdf_context, css_file_urls):
    print(settings.BASE_DIR)
    html_template = get_template(html_file_path)
    rendered_html = html_template.render(pdf_context)
    request_uri = pdf_context.get('request_uri')
    return HTML(string=rendered_html, base_url=request_uri).write_pdf(
        stylesheets=[CSS(settings.BASE_DIR + file_url) for file_url in css_file_urls]
    )
