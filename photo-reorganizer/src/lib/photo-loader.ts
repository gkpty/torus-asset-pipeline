import { Product, Photo } from '@/types';

// Sample products with actual photo paths from public directory
export const mockProducts: Product[] = [
  {
    sku: 'bed-froda-vnroak-king',
    totalImages: 2,
    photos: [
      { id: '1', filename: '1.jpg', path: '/photos/products/bed-froda-vnroak-king/1.jpg', order: 1 },
      { id: '2', filename: '2.jpg', path: '/photos/products/bed-froda-vnroak-king/2.jpg', order: 2 },
    ]
  },
  {
    sku: 'bed-froda-vnroak-queen',
    totalImages: 4,
    photos: [
      { id: '3', filename: '1.jpg', path: '/photos/products/bed-froda-vnroak-queen/1.jpg', order: 1 },
      { id: '4', filename: '2.jpg', path: '/photos/products/bed-froda-vnroak-queen/2.jpg', order: 2 },
      { id: '5', filename: '3.jpg', path: '/photos/products/bed-froda-vnroak-queen/3.jpg', order: 3 },
      { id: '6', filename: '4.jpg', path: '/photos/products/bed-froda-vnroak-queen/4.jpg', order: 4 },
    ]
  },
  {
    sku: 'bed-pure-fam-wh-king',
    totalImages: 8,
    photos: [
      { id: '7', filename: '1.jpg', path: '/photos/products/bed-pure-fam-wh-king/1.jpg', order: 1 },
      { id: '8', filename: '2.jpg', path: '/photos/products/bed-pure-fam-wh-king/2.jpg', order: 2 },
      { id: '9', filename: '3.jpg', path: '/photos/products/bed-pure-fam-wh-king/3.jpg', order: 3 },
      { id: '10', filename: '4.jpg', path: '/photos/products/bed-pure-fam-wh-king/4.jpg', order: 4 },
      { id: '11', filename: '5.jpg', path: '/photos/products/bed-pure-fam-wh-king/5.jpg', order: 5 },
    ]
  },
  {
    sku: 'bed-pure-home-gry-king',
    totalImages: 8,
    photos: [
      { id: '12', filename: '1.jpg', path: '/photos/products/bed-pure-home-gry-king/1.jpg', order: 1 },
      { id: '13', filename: '2.jpg', path: '/photos/products/bed-pure-home-gry-king/2.jpg', order: 2 },
      { id: '14', filename: '3.jpg', path: '/photos/products/bed-pure-home-gry-king/3.jpg', order: 3 },
      { id: '15', filename: '4.jpg', path: '/photos/products/bed-pure-home-gry-king/4.jpg', order: 4 },
      { id: '16', filename: '5.jpg', path: '/photos/products/bed-pure-home-gry-king/5.jpg', order: 5 },
    ]
  },
];

export function loadProducts(): Product[] {
  // In production, this would scan the file system
  return mockProducts;
}

export function loadPhotosFromDirectory(directoryPath: string): Photo[] {
  // In production, this would read from the actual directory
  // For now, return mock data
  return [];
}
