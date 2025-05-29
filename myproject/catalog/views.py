from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .forms import ProductForm
from .models import Product, Contacts, Category
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin



def home(request):
    return render(request, template_name="home.html")


def contacts(request):
    return render(request, template_name="contacts.html")


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy('catalog:product_list')

    template_name = "catalog/product_form.html"

    def get_context_data(self, **kwargs) -> dict:
        """Возвращает контекст для шаблона.
        Returns:
            dict:
        """
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context

    def form_valid(self, form) -> HttpResponse:
        """
        Обрабатывает валидацию формы.
        Args:
            form (ProductForm): _form_
        Returns:
            HttpResponse:
        """
        form.instance.owner = self.request.user
        messages.success(self.request, "Продукт успешно добавлен!")
        return super().form_valid(form)


class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy('catalog:product_list')


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


class ProductUnpublishView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "catalog.can_unpublish_product"

    def has_permission(self) -> bool:
        product = get_object_or_404(Product, pk=self.kwargs["pk"])
        return super().has_permission() or self.request.user == product.owner

    def post(self, request, pk) -> HttpResponse:
        product = get_object_or_404(Product, pk=pk)
        if product.status:
            product.status = False
            product.save()
            messages.success(request, "Продукт снят с публикации.")
        else:
            messages.warning(request, "Продукт уже снят с публикации.")
        return redirect("product", pk=pk)


class ContactsView(CreateView):
    model = Contacts
    fields = ['name', 'message']
    template_name = 'catalog/contacts.html'
    success_url = reverse_lazy('catalog:product_list')
