'use client';

import { useState, useEffect } from 'react';
import { DndContext, KeyboardSensor, PointerSensor, useSensor, useSensors, rectIntersection } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { Product, Photo, RenameInstruction, DragEndEvent } from '@/types';
import { dbManager } from '@/lib/indexeddb';
import { loadProducts } from '@/lib/photo-loader';
import ProductCard from './ProductCard';

export default function PhotoGrid() {
  const [products, setProducts] = useState<Product[]>([]);
  const [renameInstructions, setRenameInstructions] = useState<RenameInstruction>({});
  const [isLoading, setIsLoading] = useState(true);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    async function loadData() {
      try {
        await dbManager.init();
        const products = loadProducts();
        const instructions = await dbManager.getRenameInstructions();
        
        // Apply instructions to reorder photos
        const reorderedProducts = products.map(product => {
          const productInstructions = instructions[product.sku];
          if (!productInstructions) return product;
          
          // Create a mapping of what each filename should become
          const filenameMap = new Map<string, string>();
          Object.entries(productInstructions).forEach(([oldName, newName]) => {
            filenameMap.set(oldName, newName);
          });
          
          // Apply the filename mappings to create a new order
          const reorderedPhotos = product.photos.map(photo => {
            const newFilename = filenameMap.get(photo.filename) || photo.filename;
            return {
              ...photo,
              filename: newFilename
            };
          });
          
          // Sort by the new filename numbers to get the correct order
          reorderedPhotos.sort((a, b) => {
            const aNum = parseInt(a.filename.split('.')[0]);
            const bNum = parseInt(b.filename.split('.')[0]);
            return aNum - bNum;
          });
          
          return {
            ...product,
            photos: reorderedPhotos.map((photo, index) => ({
              ...photo,
              order: index + 1
            }))
          };
        });
        
        setProducts(reorderedProducts);
        setRenameInstructions(instructions);
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, []);

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
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Photo Reorganizer</h1>
          <div className="flex gap-4">
            <button
              onClick={exportInstructions}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              Export Instructions
            </button>
            <button
              onClick={clearInstructions}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              Clear Instructions
            </button>
          </div>
        </div>

        <DndContext
          sensors={sensors}
          collisionDetection={rectIntersection}
          onDragEnd={handleDragEnd}
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {products.map((product) => (
              <ProductCard key={product.sku} product={product} />
            ))}
          </div>
        </DndContext>
      </div>
    </div>
  );
}
