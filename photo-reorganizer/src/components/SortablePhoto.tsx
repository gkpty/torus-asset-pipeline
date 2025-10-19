'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Photo } from '@/types';
import { GripVertical } from 'lucide-react';

interface SortablePhotoProps {
  photo: Photo;
  sku: string;
}

export default function SortablePhoto({ photo, sku }: SortablePhotoProps) {
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
        relative group cursor-grab active:cursor-grabbing
        ${isDragging ? 'opacity-50 z-50 scale-105 shadow-lg' : 'hover:scale-105 transition-transform'}
      `}
      {...attributes}
      {...listeners}
    >
      <div className="relative aspect-square bg-gray-200 rounded-lg overflow-hidden">
        {/* Actual image */}
        <img
          src={photo.path}
          alt={photo.filename}
          className="w-full h-full object-cover"
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
            <div className="text-2xl font-bold text-gray-400 mb-2">
              {photo.order}
            </div>
            <div className="text-xs text-gray-500">
              {photo.filename}
            </div>
          </div>
        </div>
        
        {/* Drag handle */}
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="bg-white/80 backdrop-blur-sm rounded p-1 shadow-sm">
            <GripVertical className="w-4 h-4 text-gray-600" />
          </div>
        </div>

        {/* Order indicator */}
        <div className="absolute top-2 left-2">
          <div className="bg-blue-600 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
            {photo.order}
          </div>
        </div>
      </div>
    </div>
  );
}
