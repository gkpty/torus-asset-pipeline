'use client';

import { Product } from '@/types';
import { SortableContext, rectSortingStrategy } from '@dnd-kit/sortable';
import SortablePhoto from './SortablePhoto';

interface ProductCardProps {
  product: Product;
}

export default function ProductCard({ product }: ProductCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-gray-900 mb-1">
          {product.sku}
        </h2>
        <p className="text-sm text-gray-600">
          {product.totalImages} images total
        </p>
      </div>

      <SortableContext
        items={product.photos.map(photo => photo.id)}
        strategy={rectSortingStrategy}
      >
        <div className="grid grid-cols-2 gap-2">
          {product.photos.map((photo, index) => (
            <div
              key={photo.id}
              className={`${
                index === 0 ? 'col-span-2' : 'col-span-1'
              }`}
            >
              <SortablePhoto photo={photo} sku={product.sku} />
            </div>
          ))}
        </div>
      </SortableContext>
    </div>
  );
}
