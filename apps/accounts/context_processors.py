def marsa_context(request):
    user = getattr(request, "user", None)
    return {
        "marsa_role": getattr(user, "get_role_display", lambda: "")() if user and user.is_authenticated else "",
        "marsa_branch": getattr(getattr(user, "branch", None), "name", "كل الفروع") if user and user.is_authenticated else "",
    }
