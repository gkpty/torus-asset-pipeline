import PhotoGrid from '@/components/PhotoGrid';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 py-2">
      <div className="max-w-7xl mx-auto px-2 sm:px-4">
        <div className="text-center mb-4">
          <h1 className="text-xl font-bold text-gray-900 mb-1">
            Photo Reorganizer
          </h1>
          <p className="text-xs text-gray-600">
            Drag and drop photos to reorder them. Click X to remove photos beyond position 5.
          </p>
        </div>
        
        <PhotoGrid />
      </div>
    </div>
  );
}