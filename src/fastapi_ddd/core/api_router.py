from fastapi import APIRouter
from fastapi_ddd.core.config import INSTALLED_DOMAINS
from importlib import import_module

api_router = APIRouter(prefix="/api")

for domain in INSTALLED_DOMAINS:
    module_path = f"fastapi_ddd.domains.{domain}.routers"
    module = import_module(module_path)

    # Try to get 'routers' list first, fallback to single 'router'
    domain_routers = getattr(module, "routers", None)
    if domain_routers:
        for router in domain_routers:
            api_router.include_router(router)
    else:
        # Fallback for single router
        domain_router = getattr(module, "router", None)
        if domain_router:
            api_router.include_router(domain_router)
