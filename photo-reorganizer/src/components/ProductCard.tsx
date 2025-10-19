'use client';

import { Product } from '@/types';
import { SortableContext, rectSortingStrategy } from '@dnd-kit/sortable';
import SortablePhoto from './SortablePhoto';

interface ProductCardProps {
  product: Product;
  onPhotoDelete?: (sku: string, photoId: string) => void;
  onLoadMore?: (sku: string) => void;
  isExpanded?: boolean;
  onToggleExpanded?: (sku: string) => void;
}

export default function ProductCard({ product, onPhotoDelete, onLoadMore, isExpanded = false, onToggleExpanded }: ProductCardProps) {
  const photosToShow = isExpanded ? product.photos : product.photos.slice(0, 5);
  const hasMorePhotos = product.photos.length > 5;
  
  // Debug logging
  console.log(`Product ${product.sku}: Total photos: ${product.photos.length}, Showing: ${photosToShow.length}, Expanded: ${isExpanded}`);
  
  const handleLoadMore = () => {
    if (onLoadMore) {
      onLoadMore(product.sku);
    }
    if (onToggleExpanded) {
      onToggleExpanded(product.sku);
    }
  };

  const handlePhotoDelete = (photoId: string) => {
    if (onPhotoDelete) {
      onPhotoDelete(product.sku, photoId);
    }
  };

  return (
    <div className="bg-white rounded shadow-sm p-3">
      <div className="mb-3">
        <h2 className="text-base font-semibold text-gray-900 mb-1">
          {product.sku}
        </h2>
        <p className="text-sm text-gray-500">
          {product.totalImages} images
        </p>
      </div>

      <SortableContext
        items={photosToShow.map(photo => photo.id)}
        strategy={rectSortingStrategy}
      >
        <div className="grid grid-cols-2 gap-2">
          {photosToShow.map((photo, index) => (
            <div
              key={photo.id}
              className={`${
                index === 0 ? 'col-span-2' : 'col-span-1'
              }`}
            >
              <SortablePhoto 
                photo={photo} 
                sku={product.sku}
                onDelete={handlePhotoDelete}
                canDelete={true}
                isFirstImage={index === 0}
              />
            </div>
          ))}
        </div>
      </SortableContext>
      
      {/* Load more/less button */}
      {hasMorePhotos && (
        <div className="mt-2 text-center">
          <button
            onClick={handleLoadMore}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
          >
            {isExpanded 
              ? `Show less (${product.photos.length - 5} hidden)` 
              : `+${product.photos.length - 5} more photos`
            }
          </button>
        </div>
      )}
    </div>
  );
}
