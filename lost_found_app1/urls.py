from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .views import (
    CategoryViewSet,
    LostItemViewSet,
    FoundItemViewSet,
    ClaimViewSet,
    NotificationViewSet,
    manual_image_search,
    user_dashboard,
    admin_dashboard,
    verify_lost_item,
    verify_found_item,
    # image_based_search
)
# Create router and register viewsets
router= DefaultRouter()
router1= DefaultRouter()
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'profile', views.UserProfileViewSet, basename='profile')
################################################################################################
router1.register(r'categories', CategoryViewSet, basename='category')
router1.register(r'lost-items', LostItemViewSet, basename='lostitem')
router1.register(r'found-items', FoundItemViewSet, basename='founditem')
router1.register(r'claims',ClaimViewSet, basename='claim')
router1.register(r'notifications', NotificationViewSet, basename='notification')
################################################################################################
urlpatterns = [  
    # Include ViewSet routes
    path('api/', include(router.urls)),
    # JWT token refresh
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Backward compatibility endpoints
    path('api/me/', views.get_current_user, name='current-user'),
    path('api/users/', views.get_all_users, name='all-users'),
####################################################################################################
    path('', include(router1.urls)),
    ######################################################################################################
    path('dashboard/user/', user_dashboard, name='user-dashboard'),
    path('dashboard/admin/', admin_dashboard, name='admin-dashboard'),
    # Manual Image Search
    path('search/manual-image/', manual_image_search, name='manual-image-search'),
    ######################################################################################################
    # path('image-based-search/', image_based_search, name='image_based_search'),
    ########################################################################################################################
    #Admin Verification URLs
    path('admin/verify/lost-item/<uuid:item_id>/', verify_lost_item, name='verify-lost-item'),
    path('admin/verify/found-item/<uuid:item_id>/', verify_found_item, name='verify-found-item'),
    #############################################################################################################################
    #Include router URLs


]


