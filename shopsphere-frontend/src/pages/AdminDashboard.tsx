import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Edit2, Trash2, LayoutList, PackageOpen, X, RefreshCw } from 'lucide-react';
import { productService } from '../services/product.service';
import { orderService } from '../services/order.service';
import { Product, OrderStatus } from '../types';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';

export const AdminDashboard: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'products' | 'orders'>('products');
  
  // Modals & Forms State
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  
  const [prodName, setProdName] = useState('');
  const [prodDesc, setProdDesc] = useState('');
  const [prodPrice, setProdPrice] = useState<number | ''>('');
  const [prodStock, setProdStock] = useState<number | ''>('');
  const [prodCategory, setProdCategory] = useState('');
  const [prodStatus, setProdStatus] = useState<'ACTIVE' | 'INACTIVE'>('ACTIVE');
  const [prodImageUrl, setProdImageUrl] = useState('');
  
  const [isMutatingProduct, setIsMutatingProduct] = useState(false);

  // Queries
  const { data: products = [], isLoading: isProdsLoading } = useQuery({
    queryKey: ['admin-products'],
    queryFn: () => productService.getProducts(),
  });

  const { data: categories = [] } = useQuery({
    queryKey: ['admin-categories'],
    queryFn: () => productService.getCategories(),
  });

  const { data: orders = [], isLoading: isOrdersLoading } = useQuery({
    queryKey: ['admin-orders'],
    queryFn: () => orderService.listAllOrders(),
  });

  // Mutations
  const deleteProductMutation = useMutation({
    mutationFn: (id: string) => productService.deleteProduct(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-products'] });
    },
  });

  const updateOrderStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: OrderStatus }) =>
      orderService.updateOrderStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-orders'] });
    },
  });

  const handleOpenAddProduct = () => {
    setEditingProduct(null);
    setProdName('');
    setProdDesc('');
    setProdPrice('');
    setProdStock('');
    setProdCategory(categories[0]?.id || '');
    setProdStatus('ACTIVE');
    setProdImageUrl('');
    setIsProductModalOpen(true);
  };

  const handleOpenEditProduct = (product: Product) => {
    setEditingProduct(product);
    setProdName(product.name);
    setProdDesc(product.description);
    setProdPrice(product.price);
    setProdStock(product.inventory_quantity);
    setProdCategory(product.category_id);
    setProdStatus(product.status);
    setProdImageUrl(product.image_url || '');
    setIsProductModalOpen(true);
  };

  const handleSaveProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prodName || prodPrice === '' || prodStock === '') return;

    setIsMutatingProduct(true);
    const payload = {
      name: prodName,
      description: prodDesc,
      price: Number(prodPrice),
      inventory_quantity: Number(prodStock),
      category_id: prodCategory,
      status: prodStatus,
      image_url: prodImageUrl || undefined,
    };

    try {
      if (editingProduct) {
        await productService.updateProduct(editingProduct.id, payload);
      } else {
        await productService.createProduct(payload);
      }
      queryClient.invalidateQueries({ queryKey: ['admin-products'] });
      setIsProductModalOpen(false);
    } catch (err) {
      console.error('Error saving product:', err);
    } finally {
      setIsMutatingProduct(false);
    }
  };

  const handleDeleteProduct = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    try {
      await deleteProductMutation.mutateAsync(id);
    } catch (err) {
      console.error('Error deleting product:', err);
    }
  };

  const handleStatusChange = async (orderId: string, status: OrderStatus) => {
    try {
      await updateOrderStatusMutation.mutateAsync({ id: orderId, status });
    } catch (err) {
      console.error('Error updating order status:', err);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 text-textLight dark:bg-bgDark dark:text-textDark">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-borderLight pb-4 dark:border-borderDark">
        <div>
          <h1 className="font-heading text-3xl font-extrabold bg-gradient-to-r from-red-500 to-indigo-500 bg-clip-text text-transparent">
            Admin Management Center
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Admin dashboard to manage products, catalog items, and order fulfillment states.
          </p>
        </div>

        {/* Tab triggers */}
        <div className="flex rounded-lg border border-borderLight p-1 bg-cardLight dark:border-borderDark dark:bg-cardDark">
          <button
            onClick={() => setActiveTab('products')}
            className={`flex items-center gap-1.5 rounded-md px-4 py-1.5 text-xs font-bold transition-all
              ${activeTab === 'products' ? 'bg-primary text-white shadow-sm' : 'hover:bg-bgLight dark:hover:bg-borderDark'}`}
          >
            <LayoutList className="h-4 w-4" />
            Products
          </button>
          <button
            onClick={() => setActiveTab('orders')}
            className={`flex items-center gap-1.5 rounded-md px-4 py-1.5 text-xs font-bold transition-all
              ${activeTab === 'orders' ? 'bg-primary text-white shadow-sm' : 'hover:bg-bgLight dark:hover:bg-borderDark'}`}
          >
            <PackageOpen className="h-4 w-4" />
            Orders
          </button>
        </div>
      </div>

      {/* PRODUCTS TAB */}
      {activeTab === 'products' && (
        <div className="mt-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-heading text-xl font-bold">Catalog Items ({products.length})</h2>
            <Button size="sm" onClick={handleOpenAddProduct} className="flex items-center gap-1">
              <Plus className="h-4 w-4" />
              Add Product
            </Button>
          </div>

          {isProdsLoading ? (
            <div className="flex justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-borderLight bg-cardLight shadow-premium dark:border-borderDark dark:bg-cardDark">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-borderLight dark:border-borderDark">
                    <th className="py-3 px-4">Name</th>
                    <th className="py-3 px-4">Price</th>
                    <th className="py-3 px-4">Inventory Stock</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-borderLight dark:divide-borderDark text-xs">
                  {products.map((product) => (
                    <tr key={product.id} className="hover:bg-bgLight dark:hover:bg-borderDark/45 transition-colors">
                      <td className="py-3.5 px-4 font-bold">{product.name}</td>
                      <td className="py-3.5 px-4 font-semibold">${product.price.toFixed(2)}</td>
                      <td className="py-3.5 px-4 font-mono">{product.inventory_quantity} units</td>
                      <td className="py-3.5 px-4">
                        <Badge status={product.status} />
                      </td>
                      <td className="py-3.5 px-4 text-center flex justify-center gap-2">
                        <button
                          onClick={() => handleOpenEditProduct(product)}
                          className="rounded-lg p-1.5 text-blue-500 hover:bg-blue-500/10 transition-colors"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteProduct(product.id)}
                          className="rounded-lg p-1.5 text-red-500 hover:bg-red-500/10 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ORDERS TAB */}
      {activeTab === 'orders' && (
        <div className="mt-8">
          <h2 className="font-heading text-xl font-bold mb-4">Customer Orders System ({orders.length})</h2>

          {isOrdersLoading ? (
            <div className="flex justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-borderLight bg-cardLight shadow-premium dark:border-borderDark dark:bg-cardDark">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-borderLight dark:border-borderDark">
                    <th className="py-3 px-4">Order ID</th>
                    <th className="py-3 px-4">Amount</th>
                    <th className="py-3 px-4">Shipping Destination</th>
                    <th className="py-3 px-4">Fulfillment Status</th>
                    <th className="py-3 px-4 text-center">Update State</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-borderLight dark:divide-borderDark text-xs">
                  {orders.map((order) => (
                    <tr key={order.id} className="hover:bg-bgLight dark:hover:bg-borderDark/45 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold truncate max-w-[120px]">{order.id}</td>
                      <td className="py-3.5 px-4 font-bold">${order.total_price.toFixed(2)}</td>
                      <td className="py-3.5 px-4 max-w-[180px] truncate">{order.shipping_address}</td>
                      <td className="py-3.5 px-4">
                        <Badge status={order.status} />
                      </td>
                      <td className="py-3.5 px-4 text-center flex justify-center items-center">
                        <select
                          className="rounded-md border border-borderLight bg-cardLight px-2 py-1 outline-none text-xs dark:border-borderDark dark:bg-cardDark"
                          value={order.status}
                          onChange={(e) => handleStatusChange(order.id, e.target.value as OrderStatus)}
                        >
                          <option value="CREATED">CREATED</option>
                          <option value="PAID">PAID</option>
                          <option value="PROCESSING">PROCESSING</option>
                          <option value="SHIPPED">SHIPPED</option>
                          <option value="DELIVERED">DELIVERED</option>
                          <option value="CANCELLED">CANCELLED</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Add/Edit Product Modal */}
      <Modal
        isOpen={isProductModalOpen}
        onClose={() => setIsProductModalOpen(false)}
        title={editingProduct ? 'Edit Product Details' : 'Create New Product'}
      >
        <form onSubmit={handleSaveProduct} className="flex flex-col gap-4">
          <Input
            id="pname"
            label="Product Name"
            value={prodName}
            onChange={(e) => setProdName(e.target.value)}
            required
          />

          <Input
            id="pimage"
            label="Product Image URL"
            placeholder="https://example.com/image.jpg"
            value={prodImageUrl}
            onChange={(e) => setProdImageUrl(e.target.value)}
          />

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-500">Description</label>
            <textarea
              className="w-full rounded-lg border border-borderLight bg-transparent p-3 text-sm outline-none transition-all dark:border-borderDark focus:border-primary"
              rows={3}
              value={prodDesc}
              onChange={(e) => setProdDesc(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              id="pprice"
              label="Price ($)"
              type="number"
              step="0.01"
              value={prodPrice}
              onChange={(e) => setProdPrice(e.target.value !== '' ? Number(e.target.value) : '')}
              required
            />
            <Input
              id="pstock"
              label="Stock Quantity"
              type="number"
              value={prodStock}
              onChange={(e) => setProdStock(e.target.value !== '' ? Number(e.target.value) : '')}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="pcat" className="text-xs font-semibold text-slate-500">Category</label>
              <select
                id="pcat"
                className="h-10 rounded-lg border border-borderLight bg-transparent px-3 text-sm outline-none dark:border-borderDark focus:border-primary"
                value={prodCategory}
                onChange={(e) => setProdCategory(e.target.value)}
              >
                {categories.map((c) => (
                  <option key={c.id} value={c.id} className="text-slate-900">{c.name}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="pstatus" className="text-xs font-semibold text-slate-500">Status</label>
              <select
                id="pstatus"
                className="h-10 rounded-lg border border-borderLight bg-transparent px-3 text-sm outline-none dark:border-borderDark focus:border-primary"
                value={prodStatus}
                onChange={(e) => setProdStatus(e.target.value as 'ACTIVE' | 'INACTIVE')}
              >
                <option value="ACTIVE" className="text-slate-900">ACTIVE</option>
                <option value="INACTIVE" className="text-slate-900">INACTIVE</option>
              </select>
            </div>
          </div>

          <Button type="submit" variant="primary" className="mt-4" isLoading={isMutatingProduct}>
            Save Catalog Item
          </Button>
        </form>
      </Modal>
    </div>
  );
};

export default AdminDashboard;
