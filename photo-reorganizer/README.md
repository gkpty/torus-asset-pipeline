# Photo Reorganizer

A Next.js application for reorganizing product photos with drag-and-drop functionality.

## Features

- **Grid Layout**: Displays 2 products per row, each with a 2-column photo grid
- **First Photo Spanning**: The first photo in each product spans 2 columns
- **Maximum 5 Photos**: Each SKU displays a maximum of 5 photos
- **Drag & Drop**: Reorder photos within the same product by dragging
- **Rename Instructions**: Automatically generates JSON instructions for file renaming
- **IndexedDB Storage**: Saves instructions locally in the browser
- **Export Functionality**: Export rename instructions as JSON file

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. **View Products**: The app displays products in a 2-column grid layout
2. **Reorder Photos**: Drag photos within the same product to reorder them
3. **Export Instructions**: Click "Export Instructions" to download the JSON file
4. **Clear Instructions**: Click "Clear Instructions" to reset all changes

## File Structure

```
src/
├── components/
│   ├── PhotoGrid.tsx      # Main grid component
│   ├── ProductCard.tsx    # Individual product display
│   └── SortablePhoto.tsx  # Draggable photo component
├── lib/
│   ├── indexeddb.ts       # IndexedDB storage management
│   └── photo-loader.ts    # Photo loading utilities
├── types/
│   └── index.ts           # TypeScript type definitions
└── app/
    ├── layout.tsx         # Root layout
    └── page.tsx           # Home page
```

## Rename Instructions Format

The exported JSON follows this format:
```json
{
  "sku_1": {
    "1.jpg": "3.jpg",
    "3.jpg": "1.jpg"
  },
  "sku_2": {
    "2.jpg": "4.jpg",
    "4.jpg": "2.jpg"
  }
}
```

## Technologies Used

- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **@dnd-kit** - Drag and drop functionality
- **IndexedDB** - Local storage
- **Lucide React** - Icons

## Development

The app currently uses mock data for development. To integrate with real photo data:

1. Update `src/lib/photo-loader.ts` to load from actual file system
2. Modify the photo loading logic to scan your photo directories
3. Update the image display to show actual photos instead of placeholders