async def main(request, templates, **kwargs):
    return templates.TemplateResponse(request, "main.j2")
