'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Photo } from '@/types';
import { GripVertical, X } from 'lucide-react';

interface SortablePhotoProps {
  photo: Photo;
  sku: string;
  onDelete?: (photoId: string) => void;
  canDelete?: boolean;
  isFirstImage?: boolean;
}

export default function SortablePhoto({ photo, sku, onDelete, canDelete = false, isFirstImage = false }: SortablePhotoProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ 
    id: photo.id,
    data: {
      sku: sku
    }
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`
        relative group
        ${isDragging ? 'opacity-50 z-50 scale-105 shadow-lg' : 'hover:scale-105 transition-transform'}
      `}
      {...attributes}
    >
      <div className="relative bg-gray-200 overflow-hidden" style={{ height: isFirstImage ? '160px' : '120px' }}>
        {/* Actual image */}
        <img
          src={photo.path}
          alt={photo.filename}
          className="w-full h-full object-contain"
          onError={(e) => {
            // Fallback to placeholder if image fails to load
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
            const fallback = target.nextElementSibling as HTMLElement;
            if (fallback) fallback.style.display = 'flex';
          }}
        />
        {/* Fallback placeholder */}
        <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200" style={{ display: 'none' }}>
          <div className="text-center">
            <div className="text-lg font-bold text-gray-400 mb-1">
              {photo.order}
            </div>
            <div className="text-xs text-gray-500">
              {photo.filename}
            </div>
          </div>
        </div>
        
        {/* Drag handle */}
        <div 
          className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing z-10"
          {...listeners}
        >
          <div className="bg-white/90 backdrop-blur-sm p-1 shadow-sm">
            <GripVertical className="w-3 h-3 text-gray-600" />
          </div>
        </div>

        {/* Delete button */}
        {canDelete && onDelete && (
          <div className="absolute top-1 left-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onDelete(photo.id);
              }}
              onMouseDown={(e) => {
                e.preventDefault();
                e.stopPropagation();
              }}
              className="bg-red-500 hover:bg-red-600 text-white p-1 shadow-sm transition-colors"
              title="Remove this photo"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        )}

        {/* Order indicator */}
        <div className="absolute bottom-1 right-1">
          <div className="bg-blue-600 text-white text-xs font-bold w-5 h-5 flex items-center justify-center">
            {photo.order}
          </div>
        </div>
      </div>
    </div>
  );
}
