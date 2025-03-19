from rest_framework.routers import DefaultRouter
from .views import TripPlanViewSet
from django.urls import path, include


router = DefaultRouter()
router.register('trip-plan', TripPlanViewSet, basename='trip-plan')

urlpatterns = [
    path('', include(router.urls)),
]