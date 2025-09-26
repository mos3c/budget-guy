# from django.urls import path, include
# from rest_framework_simplejwt.views import TokenRefreshView
# from .views import RegisterView, LoginView, LogoutView, CategoryViewSet
# from rest_framework.routers import DefaultRouter
# from .views import TransactionViewSet, BudgetViewSet, InvestmentViewSet, DashboardAnalyticsView, MonthlySummaryView, CategoryBreakdownView, InvestmentPerformanceView, BudgetProgressView

# router = DefaultRouter()
# router.register(r'categories', CategoryViewSet, basename='category')
# router.register(r'transactions', TransactionViewSet, basename='transaction')
# router.register(r'budgets', BudgetViewSet, basename='budget')
# router.register(r'investments', InvestmentViewSet, basename='investment')

# urlpatterns = [
#     path('auth/register/', RegisterView.as_view(), name='register'),
#     path('auth/login/', LoginView.as_view(), name='login'),
#     path('auth/logout/', LogoutView.as_view(), name='logout'),
#     path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('analytics/dashboard/', DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
#     path('analytics/monthly-summary/', MonthlySummaryView.as_view(), name='monthly-summary'),
#     path('analytics/category-breakdown/', CategoryBreakdownView.as_view(), name='category-breakdown'),
#     path('analytics/investment-performance/', InvestmentPerformanceView.as_view(), name='investment-performance'),
#     path('analytics/budget-progress/', BudgetProgressView.as_view(), name='budget-progress'),
#     path('', include(router.urls))
    
# 

from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, LogoutView,
    CategoryViewSet, TransactionViewSet,
    BudgetViewSet, InvestmentViewSet,
    DashboardAnalyticsView, MonthlySummaryView,
    CategoryBreakdownView, InvestmentPerformanceView,
    BudgetProgressView
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'investments', InvestmentViewSet, basename='investment')

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('analytics/dashboard/', DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
    path('analytics/monthly-summary/', MonthlySummaryView.as_view(), name='monthly-summary'),
    path('analytics/category-breakdown/', CategoryBreakdownView.as_view(), name='category-breakdown'),
    path('analytics/investment-performance/', InvestmentPerformanceView.as_view(), name='investment-performance'),
    path('analytics/budget-progress/', BudgetProgressView.as_view(), name='budget-progress'),

    path('', include(router.urls)),

    # Transactions export placeholders (added for frontend expectations)
    path('transactions/export_csv/', TransactionViewSet.as_view({'get': 'export_csv'}), name='transaction-export-csv'),
    path('transactions/export_pdf/', TransactionViewSet.as_view({'get': 'export_pdf'}), name='transaction-export-pdf'),
]
