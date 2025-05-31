from django.http import HttpResponse
from django.views import View

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


class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        queryset = cache.get('products')
        if not queryset:
            queryset = super().get_queryset()
            cache.set('products', queryset, 60 * 15)  # Кешируем данные на 15 минут
        return queryset


class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        cache_key = f'product_detail_{pk}'
        product = cache.get(cache_key)

        if product is None:
            product = super().get_object(queryset)
            cache.set(cache_key, product, timeout=60 * 5)  # 5 минут

        return product

    @method_decorator(cache_page(60 * 15), name='dispatch')  # Кэширование страницы на 15 минут
    class ProductDetailView(DetailView):
        model = Product
        template_name = 'catalog/product_detail.html'
        context_object_name = 'product'


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/add_product.html'
    success_url = reverse_lazy('catalog:product_list')


# class ProductDeleteView(LoginRequiredMixin, DeleteView):
#     model = Product
#     template_name = 'catalog/product_confirm_delete.html'
#     success_url = reverse_lazy('catalog:product_list')
#     context_object_name = "product"
#
#     @method_decorator(permission_required('products.delete_product', raise_exception=True))
#     def dispatch(self, request, *args, **kwargs):
#         product = self.get_object()
#
#         # Проверяем, что пользователь либо владелец, либо имеет право на удаление
#         if product.owner != request.user and not request.user.has_perm('products.delete_product'):
#             raise PermissionDenied("Вы не можете удалить этот продукт.")
#
#         return super().dispatch(request, *args, **kwargs)

class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('catalog:product_list')
    context_object_name = "product"
    permission_required = "catalog.can_delete_product"

    def has_permission(self) -> bool:
        product = get_object_or_404(Product, pk=self.kwargs["pk"])
        return super().has_permission() or self.request.user == product.owner

    def delete(self, request, *args, **kwargs) -> HttpResponse:
        messages.success(self.request, "Продукт успешно удалён!")
        return super().delete(request, *args, **kwargs)

# class ProductUnpublishView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     permission_required = "catalog.can_unpublish_product"
#
#     def has_permission(self) -> bool:
#         product = get_object_or_404(Product, pk=self.kwargs["pk"])
#         return super().has_permission() or self.request.user == product.owner
#
#     def post(self, request, pk) -> HttpResponse:
#         product = get_object_or_404(Product, pk=pk)
#         if product.status:
#             product.status = False
#             product.save()
#             messages.success(request, "Продукт снят с публикации.")
#         else:
#             messages.warning(request, "Продукт уже снят с публикации.")
#         return redirect("product", pk=pk)


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
