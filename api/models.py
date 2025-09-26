from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Create your models here.
class Category(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense')
    ]
    # id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        verbose_name_plural = 'Categories'
        unique_together =  ('user', 'name', 'type') 
        
    def __str__(self):
        return f"{self.name} ({self.type})"
    
class Transaction(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True ,blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Transactions'
        ordering = ['-date', '-created_at'] #newest first
        
    def __str__(self):
        return f"${self.amount} - {self.category.name} ({self.date})"
    
    def clean(self):
        # Validate that transaction type matches category type
        if self.category and self.type != self.category.type:
            raise ValidationError(f'Transaction type must match category type ({self.category.type})')
    
class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    monthly_limit = models.DecimalField(max_digits=10, decimal_places=2) 
    month = models.IntegerField(choices=[(i, i) for i in range(1, 13)])  # 1-12 for months
    year = models.IntegerField() 
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Budgets'
        unique_together = ('user', 'category', 'month', 'year')  # One budget per category per month
       
    def __str__(self):
        return f"{self.category.name} - {self.month}/{self.year} (${self.monthly_limit})"


class Investment(models.Model):
    INVESTMENT_CHOICES = [  
        ('stocks', 'Stocks'),
        ('crypto', 'Crypto'),
        ('real_estate', 'Real Estate'),  
        ('others', 'Others')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=30, choices=INVESTMENT_CHOICES)
    others = models.TextField(null=True, blank=True) 
    amount_invested = models.DecimalField(max_digits=15, decimal_places=2)
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    quantity = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True) 
    purchase_date = models.DateField()  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Investments'  
        ordering = ['-purchase_date']
       
    def __str__(self):
        return f"{self.name} - ${self.current_value}"
    
    @property
    def profit_loss(self):
        return self.current_value - self.amount_invested
    
    @property
    def profit_loss_percentage(self):
        if self.amount_invested > 0:
            return ((self.current_value - self.amount_invested) / self.amount_invested) * 100
        return 0
    
