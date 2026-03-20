from fastapi import FastAPI

from portfolio.models import Profile, ResourceItem

fastapi_app = FastAPI(title="karra.ai API", version="1.0.0")


@fastapi_app.get("/health")
def health_check():
    return {"status": "ok"}


@fastapi_app.get("/profile")
def profile():
    profile_obj = Profile.objects.first()
    if not profile_obj:
        return {"message": "Profile not synced yet."}

    return {
        "name": profile_obj.name,
        "github_username": profile_obj.github_username,
        "bio": profile_obj.bio,
        "location": profile_obj.location,
        "avatar_url": profile_obj.avatar_url,
        "github_url": profile_obj.github_url,
        "followers": profile_obj.followers,
        "public_repos": profile_obj.public_repos,
    }


@fastapi_app.get("/resources")
def resources(domain: str | None = None):
    queryset = ResourceItem.objects.all()
    if domain:
        queryset = queryset.filter(domain=domain)

    data = [
        {
            "domain": item.domain,
            "category": item.category,
            "title": item.title,
            "description": item.description,
            "url": item.url,
            "entangled": item.entangled_with_other_domain,
        }
        for item in queryset
    ]
    return {"count": len(data), "items": data}
