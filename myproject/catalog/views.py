from django.http import HttpResponse
from .forms import ProductForm
from .models import Product, Contacts, Category
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.core.cache import cache
from catalog.services import get_products_by_category
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


def home(request):
    return render(request, template_name="home.html")


def contacts(request):
    return render(request, template_name="contacts.html")


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "catalog/add_product.html"
    success_url = reverse_lazy('catalog:product_list')

    def get_context_data(self, **kwargs) -> dict:
        """Возвращает контекст для шаблона"""
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context

    def form_valid(self, form) -> HttpResponse:
        """ Обрабатывает валидацию формы"""
        form.instance.owner = self.request.user
        messages.success(self.request, "Продукт успешно добавлен!")
        return super().form_valid(form)


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        queryset = cache.get('products')
        if not queryset:
            queryset = super().get_queryset()
            cache.set('products', queryset, 60 * 15)  # Кешируем данные на 15 минут
        return queryset


@method_decorator(cache_page(60 * 15), name='dispatch')
class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/add_product.html'
    success_url = reverse_lazy('catalog:product_list')

    def get_form_class(self):
        user = self.request.user
        if user == self.object.owner:
            return ProductForm
        raise PermissionDenied


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'catalog/product_confirm_delete.html'
    success_url = reverse_lazy('catalog:product_list')


    def get_form_class(self):
        user = self.request.user
        if user == self.object.owner or user.groups.filter(name= 'Модератор продуктов').exists():
            return ProductForm
        raise PermissionDenied


@login_required
@permission_required('catalog.can_unpublish_product', raise_exception=True)
def unpublish_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.status = 'draft'
        product.save()
        return redirect('catalog:product_list')
    return render(request, 'catalog/unpublish_product.html', {'product': product})


class ContactsView(CreateView):
    model = Contacts
    fields = ['name', 'message']
    template_name = 'catalog/contacts.html'
    success_url = reverse_lazy('catalog:product_list')


class ProductsByCategoryView(ListView):
    template_name = 'catalog/prod_in_category.html'
    context_object_name = 'products'

    def get_queryset(self):
        category = self.kwargs.get('category')
        return get_products_by_category(category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = Category.objects.get(id=self.kwargs.get('category_id'))
        return context
