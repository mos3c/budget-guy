from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.decorators import action
from .serializers import RegisterSerializer, LoginSerializer, CategorySerializer, TransactionSerializer, BudgetSerializer, InvestmentSerializer
from .models import Category, Transaction, Budget, Investment
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime
from django.utils import timezone
from django.db.models import Sum
from rest_framework import filters
from django.http import HttpResponse
from io import BytesIO
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter



class RegisterView(APIView):
    permission_classes = []
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = []
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['types', 'is_ative']
    
    def get_queryset(self):
        return Category.object.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # category is tied to a login user
        serializer.save(user=self.request.user)
        
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'category', 'date']
    search_fields = ['description', 'category__name', 'amount']
    ordering_fields = ['date', 'amount', 'created_at', 'category__name']
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export transactions to CSV"""
        transactions = self.get_queryset()
        transactions = self.filter_queryset(transactions)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Type', 'Category', 'Amount', 'Description', 'Created'])
        
        for transaction in transactions:
            writer.writerow([
                transaction.date,
                transaction.type,
                transaction.category.name,
                transaction.amount,
                transaction.description or '',
                transaction.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
    
    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        """Export transactions to PDF"""
        transactions = self.get_queryset()
        transactions = self.filter_queryset(transactions)
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, f"Transaction Report - {request.user.username}")
        
        # Summary
        total_income = sum(t.amount for t in transactions if t.type == 'income')
        total_expenses = sum(t.amount for t in transactions if t.type == 'expense')
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 80, f"Total Income: ${total_income}")
        p.drawString(200, height - 80, f"Total Expenses: ${total_expenses}")
        p.drawString(350, height - 80, f"Net: ${total_income - total_expenses}")
        
        # Headers
        p.setFont("Helvetica-Bold", 10)
        y = height - 120
        p.drawString(50, y, "Date")
        p.drawString(120, y, "Type")
        p.drawString(180, y, "Category")
        p.drawString(280, y, "Amount")
        p.drawString(350, y, "Description")
        
        # Data
        p.setFont("Helvetica", 9)
        y -= 20
        
        for transaction in transactions:
            if y < 50:
                p.showPage()
                y = height - 50
            
            p.drawString(50, y, str(transaction.date))
            p.drawString(120, y, transaction.type)
            p.drawString(180, y, transaction.category.name[:15])
            p.drawString(280, y, f"${transaction.amount}")
            description = transaction.description or ''
            p.drawString(350, y, description[:20])
            y -= 15
        
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="transactions.pdf"'
        return response
        
    

class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    pagination_class = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_field = ['category', 'month', 'year', 'is_active']
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class InvestmentViewSet(viewsets.ModelViewSet):
    serializer_class = InvestmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type', 'purchase_date']

    def get_queryset(self):
        return Investment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
class DashboardAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        current_date = timezone.now().date()
        current_month = current_date.month
        current_year = current_date.year
        
        # Current month transactions
        current_month_transactions = Transaction.objects.filter(
            user=user,
            date__month=current_month,
            date__year=current_year
        )
        
        # Total income and expenses for current month
        monthly_income = current_month_transactions.filter(type='income').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        monthly_expenses = current_month_transactions.filter(type='expense').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Current balance (all time)
        all_income = Transaction.objects.filter(user=user, type='income').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        all_expenses = Transaction.objects.filter(user=user, type='expense').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        current_balance = all_income - all_expenses
        
        # Top spending categories (current month)
        top_categories = (
            current_month_transactions
            .filter(type='expense')
            .values('category__name')
            .annotate(total_spent=Sum('amount'))
            .order_by('-total_spent')[:5]
        )
        
        # Recent transactions (last 5)
        recent_transactions = Transaction.objects.filter(user=user).order_by('-date', '-created_at')[:5]
        recent_transactions_data = [
            {
                'id': t.id,
                'amount': float(t.amount),
                'type': t.type,
                'category': t.category.name,
                'description': t.description,
                'date': t.date
            }
            for t in recent_transactions
        ]
        
        # Investment portfolio value
        investments = Investment.objects.filter(user=user)
        total_invested = investments.aggregate(total=Sum('amount_invested'))['total'] or 0
        total_current_value = investments.aggregate(total=Sum('current_value'))['total'] or 0
        portfolio_gain_loss = total_current_value - total_invested
        
        # Budget progress (current month)
        current_budgets = Budget.objects.filter(
            user=user,
            month=current_month,
            year=current_year,
            is_active=True
        )
        
        budget_progress = []
        for budget in current_budgets:
            spent = current_month_transactions.filter(
                category=budget.category,
                type='expense'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            progress_percentage = (spent / budget.monthly_limit * 100) if budget.monthly_limit > 0 else 0
            
            budget_progress.append({
                'category': budget.category.name,
                'budgeted': float(budget.monthly_limit),
                'spent': float(spent),
                'remaining': float(budget.monthly_limit - spent),
                'progress_percentage': round(progress_percentage, 2),
                'is_over_budget': spent > budget.monthly_limit
            })
        
        return Response({
            'current_month_summary': {
                'income': float(monthly_income),
                'expenses': float(monthly_expenses),
                'net_income': float(monthly_income - monthly_expenses),
                'month': current_month,
                'year': current_year
            },
            'overall_summary': {
                'total_balance': float(current_balance),
                'total_invested': float(total_invested),
                'portfolio_value': float(total_current_value),
                'portfolio_gain_loss': float(portfolio_gain_loss)
            },
            'top_spending_categories': [
                {
                    'category': cat['category__name'],
                    'amount': float(cat['total_spent'])
                }
                for cat in top_categories
            ],
            'recent_transactions': recent_transactions_data,
            'budget_progress': budget_progress
        })
        
class MonthlySummaryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        current_year = timezone.now().year
        year = int(request.GET.get('year', current_year))
        
        monthly_data = []
        
        for month in range(1, 13):
            month_transactions = Transaction.objects.filter(
                user=user,
                date__month=month,
                date__year=year
            )
            
            income = month_transactions.filter(type='income').aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            expenses = month_transactions.filter(type='expense').aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            monthly_data.append({
                'month': month,
                'income': float(income),
                'expenses': float(expenses),
                'net_income': float(income - expenses)
            })
        
        return Response({
            'year': year,
            'monthly_summary': monthly_data
        })
        
class CategoryBreakdownView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Filter transactions by date range
        transactions = Transaction.objects.filter(user=user)
        if start_date:
            transactions = transactions.filter(date__gte=start_date)
        if end_date:
            transactions = transactions.filter(date__lte=end_date)
        
        # Income breakdown
        income_breakdown = (
            transactions.filter(type='income')
            .values('category__name')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        
        # Expense breakdown
        expense_breakdown = (
            transactions.filter(type='expense')
            .values('category__name')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        
        return Response({
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'income_by_category': [
                {
                    'category': item['category__name'],
                    'amount': float(item['total'])
                }
                for item in income_breakdown
            ],
            'expenses_by_category': [
                {
                    'category': item['category__name'],
                    'amount': float(item['total'])
                }
                for item in expense_breakdown
            ]
        })
        
class InvestmentPerformanceView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        investments = Investment.objects.filter(user=user)
        
        # Overall portfolio summary
        total_invested = investments.aggregate(total=Sum('amount_invested'))['total'] or 0
        total_current_value = investments.aggregate(total=Sum('current_value'))['total'] or 0
        total_profit_loss = total_current_value - total_invested
        
        # Calculate overall percentage return
        overall_return_percentage = 0
        if total_invested > 0:
            overall_return_percentage = (total_profit_loss / total_invested) * 100
        
        # Individual investment performance
        individual_investments = []
        for investment in investments:
            individual_investments.append({
                'id': investment.id,
                'name': investment.name,
                'type': investment.type,
                'amount_invested': float(investment.amount_invested),
                'current_value': float(investment.current_value),
                'profit_loss': float(investment.profit_loss),
                'profit_loss_percentage': float(investment.profit_loss_percentage),
                'purchase_date': investment.purchase_date
            })
        
        # Performance by investment type
        type_performance = (
            investments.values('type')
            .annotate(
                total_invested=Sum('amount_invested'),
                total_current_value=Sum('current_value')
            )
        )
        
        type_breakdown = []
        for item in type_performance:
            invested = item['total_invested'] or 0
            current = item['total_current_value'] or 0
            profit_loss = current - invested
            percentage = (profit_loss / invested * 100) if invested > 0 else 0
            
            type_breakdown.append({
                'type': item['type'],
                'total_invested': float(invested),
                'total_current_value': float(current),
                'profit_loss': float(profit_loss),
                'profit_loss_percentage': round(percentage, 2)
            })
        
        return Response({
            'portfolio_summary': {
                'total_invested': float(total_invested),
                'total_current_value': float(total_current_value),
                'total_profit_loss': float(total_profit_loss),
                'overall_return_percentage': round(overall_return_percentage, 2)
            },
            'individual_investments': individual_investments,
            'performance_by_type': type_breakdown
        })
        
class BudgetProgressView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        current_date = timezone.now().date()
        month = int(request.GET.get('month', current_date.month))
        year = int(request.GET.get('year', current_date.year))
        
        # Get budgets for the specified month/year
        budgets = Budget.objects.filter(
            user=user,
            month=month,
            year=year,
            is_active=True
        )
        
        # Get transactions for the same period
        transactions_in_period = Transaction.objects.filter(
            user=user,
            date__month=month,
            date__year=year,
            type='expense'
        )
        
        budget_progress = []
        total_budgeted = 0
        total_spent = 0
        
        for budget in budgets:
            # Calculate spending for this budget's category
            spent = transactions_in_period.filter(
                category=budget.category
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            remaining = budget.monthly_limit - spent
            progress_percentage = (spent / budget.monthly_limit * 100) if budget.monthly_limit > 0 else 0
            is_over_budget = spent > budget.monthly_limit
            
            budget_progress.append({
                'category_id': budget.category.id,
                'category_name': budget.category.name,
                'budgeted_amount': float(budget.monthly_limit),
                'spent_amount': float(spent),
                'remaining_amount': float(remaining),
                'progress_percentage': round(progress_percentage, 2),
                'is_over_budget': is_over_budget,
                'days_left_in_month': self.get_days_left_in_month(month, year)
            })
            
            total_budgeted += budget.monthly_limit
            total_spent += spent
        
        # Overall budget summary
        overall_progress = (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0
        overall_remaining = total_budgeted - total_spent
        
        return Response({
            'period': {
                'month': month,
                'year': year
            },
            'overall_summary': {
                'total_budgeted': float(total_budgeted),
                'total_spent': float(total_spent),
                'total_remaining': float(overall_remaining),
                'overall_progress_percentage': round(overall_progress, 2),
                'is_over_overall_budget': total_spent > total_budgeted
            },
            'category_progress': budget_progress,
            'categories_without_budget': self.get_categories_without_budget(user, month, year)
        })
    
    def get_days_left_in_month(self, month, year):
        from calendar import monthrange
        current_date = timezone.now().date()
        
        if current_date.month == month and current_date.year == year:
            days_in_month = monthrange(year, month)[1]
            return days_in_month - current_date.day
        return 0
    
    def get_categories_without_budget(self, user, month, year):
        # Find expense categories that have transactions but no budget
        from .models import Category
        
        transactions_in_period = Transaction.objects.filter(
            user=user,
            date__month=month,
            date__year=year,
            type='expense'
        )
        
        categories_with_spending = transactions_in_period.values_list('category_id', flat=True).distinct()
        categories_with_budget = Budget.objects.filter(
            user=user,
            month=month,
            year=year,
            is_active=True
        ).values_list('category_id', flat=True)
        
        categories_without_budget = Category.objects.filter(
            id__in=categories_with_spending
        ).exclude(
            id__in=categories_with_budget
        )
        
        result = []
        for category in categories_without_budget:
            spent = transactions_in_period.filter(
                category=category
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            result.append({
                'category_id': category.id,
                'category_name': category.name,
                'spent_amount': float(spent)
            })
        
        return result
    
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'category', 'date']
    search_fields = ['description', 'category__name', 'amount']  # Search in these fields
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date']  # Default ordering
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)