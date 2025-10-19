'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { DndContext, KeyboardSensor, PointerSensor, useSensor, useSensors, rectIntersection } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { Product, Photo, RenameInstruction, DragEndEvent } from '@/types';
import { dbManager } from '@/lib/indexeddb';
import ProductCard from './ProductCard';

export default function PhotoGrid() {
  const [products, setProducts] = useState<Product[]>([]);
  const [renameInstructions, setRenameInstructions] = useState<RenameInstruction>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [expandedProducts, setExpandedProducts] = useState<Set<string>>(new Set());
  const [pagination, setPagination] = useState({
    page: 1,
    totalPages: 1,
    hasNext: false,
    hasPrev: false
  });
  const [searchTerm, setSearchTerm] = useState('');
  const observerRef = useRef<HTMLDivElement>(null);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Load products from API
  const loadProductsFromAPI = useCallback(async (page: number = 1, search: string = '', append: boolean = false) => {
    try {
      if (append) {
        setIsLoadingMore(true);
      } else {
        setIsLoading(true);
      }

      const params = new URLSearchParams({
        page: page.toString(),
        limit: '12',
        ...(search && { search })
      });

      console.log('Fetching products:', `/api/products?${params}`);
      const response = await fetch(`/api/products?${params}`);
      if (!response.ok) {
        throw new Error('Failed to load products');
      }

      const data = await response.json();
      console.log('API response:', {
        productsCount: data.products.length,
        pagination: data.pagination,
        append
      });
      
      // Load rename instructions from IndexedDB
      await dbManager.init();
      const instructions = await dbManager.getRenameInstructions();
      setRenameInstructions(instructions);

      // Apply rename instructions to products
      const updatedProducts = data.products.map((product: Product) => {
        const productInstructions = instructions[product.sku];
        if (!productInstructions) return product;

        // Apply filename mappings and reorder
        const updatedPhotos = product.photos.map(photo => {
          const newFilename = productInstructions[photo.filename] || photo.filename;
          return { ...photo, filename: newFilename };
        });

        // Sort by new filenames (1.jpg, 2.jpg, etc.)
        updatedPhotos.sort((a, b) => {
          const aNum = parseInt(a.filename.split('.')[0]);
          const bNum = parseInt(b.filename.split('.')[0]);
          return aNum - bNum;
        });

        // Update order based on new positions
        const reorderedPhotos = updatedPhotos.map((photo, index) => ({
          ...photo,
          order: index + 1
        }));

        return {
          ...product,
          photos: reorderedPhotos
        };
      });

      if (append) {
        setProducts(prev => {
          const existingSkus = new Set(prev.map(p => p.sku));
          const newProducts = updatedProducts.filter(p => !existingSkus.has(p.sku));
          return [...prev, ...newProducts];
        });
      } else {
        setProducts(updatedProducts);
      }
      
      setPagination({
        page: data.pagination.page,
        totalPages: data.pagination.totalPages,
        hasNext: data.pagination.hasNext,
        hasPrev: data.pagination.hasPrev
      });

    } catch (error) {
      console.error('Error loading products:', error);
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadProductsFromAPI(1, searchTerm);
  }, [loadProductsFromAPI, searchTerm]);

  // Infinite scroll observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        console.log('Intersection observer triggered:', {
          isIntersecting: entries[0].isIntersecting,
          hasNext: pagination.hasNext,
          isLoadingMore,
          currentPage: pagination.page
        });
        
        if (entries[0].isIntersecting && pagination.hasNext && !isLoadingMore) {
          console.log('Loading more products...');
          loadProductsFromAPI(pagination.page + 1, searchTerm, true);
        }
      },
      { threshold: 0.1 }
    );

    if (observerRef.current) {
      observer.observe(observerRef.current);
    }

    return () => observer.disconnect();
  }, [pagination.hasNext, isLoadingMore, loadProductsFromAPI, searchTerm, pagination.page]);

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    const activeSku = active.data.current.sku;
    const overSku = over.data.current.sku;

    // Only allow reordering within the same product
    if (activeSku !== overSku) {
      return;
    }

    const productIndex = products.findIndex(p => p.sku === activeSku);
    if (productIndex === -1) {
      return;
    }

    const product = products[productIndex];
    const activeIndex = product.photos.findIndex(p => p.id === active.id);
    const overIndex = product.photos.findIndex(p => p.id === over.id);

    if (activeIndex === -1 || overIndex === -1) {
      return;
    }

    // Update the product's photo order
    const newPhotos = arrayMove(product.photos, activeIndex, overIndex);
    const updatedProduct = {
      ...product,
      photos: newPhotos.map((photo, index) => ({ ...photo, order: index + 1 }))
    };

    // Update products state
    const newProducts = [...products];
    newProducts[productIndex] = updatedProduct;
    setProducts(newProducts);

    // Update rename instructions
    const activePhoto = product.photos[activeIndex];
    const overPhoto = product.photos[overIndex];

    const newInstructions = { ...renameInstructions };
    if (!newInstructions[activeSku]) {
      newInstructions[activeSku] = {};
    }

    // Create rename instructions for the swap
    newInstructions[activeSku][activePhoto.filename] = overPhoto.filename;
    newInstructions[activeSku][overPhoto.filename] = activePhoto.filename;

    setRenameInstructions(newInstructions);

    // Save to IndexedDB
    try {
      await dbManager.saveRenameInstructions(newInstructions);
    } catch (error) {
      console.error('Error saving rename instructions:', error);
    }
  };

  const handleLoadMore = (sku: string) => {
    // This could be used to load more photos from a server if needed
    // For now, it's just handled by the local state in ProductCard
    console.log(`Loading more photos for ${sku}`);
  };

  const handleToggleExpanded = (sku: string) => {
    setExpandedProducts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sku)) {
        newSet.delete(sku);
      } else {
        newSet.add(sku);
      }
      return newSet;
    });
  };

  const handlePhotoDelete = async (sku: string, photoId: string) => {
    const productIndex = products.findIndex(p => p.sku === sku);
    if (productIndex === -1) {
      return;
    }

    const product = products[productIndex];
    const photoToDelete = product.photos.find(p => p.id === photoId);
    if (!photoToDelete) {
      return;
    }

    // Find the index of the photo to delete
    const deleteIndex = product.photos.findIndex(p => p.id === photoId);
    
    console.log(`Deleting photo at index ${deleteIndex} from product ${sku}`);
    console.log(`Before deletion: ${product.photos.length} photos`);
    
    // Remove the photo from the product
    const newPhotos = product.photos.filter(p => p.id !== photoId);
    
    console.log(`After deletion: ${newPhotos.length} photos`);
    console.log(`First 5 photos after deletion:`, newPhotos.slice(0, 5).map(p => ({ id: p.id, filename: p.filename, order: p.order })));
    
    // Create rename instructions for the deletion
    const newInstructions = { ...renameInstructions };
    if (!newInstructions[sku]) {
      newInstructions[sku] = {};
    }

    // Generate rename instructions:
    // 1. All photos after the deleted photo move up one position
    // 2. The deleted photo moves to the last position
    const deletedPhotoFilename = photoToDelete.filename;
    const lastPosition = newPhotos.length; // This will be the new last position
    
    // Move all photos after the deleted one up by one position
    for (let i = deleteIndex + 1; i < product.photos.length; i++) {
      const currentPhoto = product.photos[i];
      const newPosition = i; // Move up one position (i instead of i+1)
      const newFilename = `${newPosition}.jpg`;
      
      // Only create instruction if the filename would actually change
      if (currentPhoto.filename !== newFilename) {
        newInstructions[sku][currentPhoto.filename] = newFilename;
      }
    }
    
    // Move the deleted photo to the last position
    const deletedPhotoNewFilename = `${lastPosition + 1}.jpg`;
    newInstructions[sku][deletedPhotoFilename] = deletedPhotoNewFilename;

    // Smart reordering: if we deleted from the first 5 photos and there are more photos available,
    // the photos array is already in the correct order, we just need to renumber them
    const finalPhotos = newPhotos.map((photo, index) => ({ 
      ...photo, 
      order: index + 1 
    }));

    const updatedProduct = {
      ...product,
      photos: finalPhotos,
      totalImages: finalPhotos.length
    };

    // Update products state
    const newProducts = [...products];
    newProducts[productIndex] = updatedProduct;
    setProducts(newProducts);

    setRenameInstructions(newInstructions);

    // Save to IndexedDB
    try {
      await dbManager.saveRenameInstructions(newInstructions);
      console.log('Rename instructions saved:', newInstructions[sku]);
    } catch (error) {
      console.error('Error saving rename instructions:', error);
    }
  };

  const exportInstructions = () => {
    const dataStr = JSON.stringify(renameInstructions, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = 'rename-instructions.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const clearInstructions = async () => {
    try {
      await dbManager.clearRenameInstructions();
      setRenameInstructions({});
    } catch (error) {
      console.error('Error clearing instructions:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading products...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-gray-900">
            Products ({products.length})
          </h2>
          <p className="text-xs text-gray-600 mt-1">
            Drag and drop to reorder photos within each product
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={exportInstructions}
            className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs font-medium transition-colors"
          >
            Export
          </button>
          <button
            onClick={clearInstructions}
            className="bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-xs font-medium transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Search input */}
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Search products..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

        <DndContext
          sensors={sensors}
          collisionDetection={rectIntersection}
          onDragEnd={handleDragEnd}
        >
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {products.map((product) => (
            <ProductCard 
              key={product.sku} 
              product={product} 
              onPhotoDelete={handlePhotoDelete}
              onLoadMore={handleLoadMore}
              isExpanded={expandedProducts.has(product.sku)}
              onToggleExpanded={handleToggleExpanded}
            />
          ))}
        </div>
        </DndContext>

      {/* Infinite scroll trigger */}
      <div ref={observerRef} className="flex justify-center py-4 min-h-[50px]">
        {pagination.hasNext ? (
          isLoadingMore ? (
            <div className="text-sm text-gray-500">Loading more products...</div>
          ) : (
            <div className="text-sm text-gray-400">Scroll down to load more</div>
          )
        ) : (
          <div className="text-sm text-gray-400">No more products to load</div>
        )}
      </div>

    </div>
  );
}
