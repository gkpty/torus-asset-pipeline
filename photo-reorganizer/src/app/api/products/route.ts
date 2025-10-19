import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '12');
    const search = searchParams.get('search') || '';

    console.log('API called with params:', { page, limit, search });

    const productsDir = path.join(process.cwd(), 'public', 'photos', 'products');
    
    // Read all product directories
    const productDirs = fs.readdirSync(productsDir, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name)
      .filter(name => !name.startsWith('.')) // Filter out hidden directories
      .sort();

    // Filter by search term if provided
    const filteredDirs = search 
      ? productDirs.filter(dir => dir.toLowerCase().includes(search.toLowerCase()))
      : productDirs;

    // Calculate pagination
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedDirs = filteredDirs.slice(startIndex, endIndex);

    // Process each product directory
    const products = await Promise.all(
      paginatedDirs.map(async (sku) => {
        const productPath = path.join(productsDir, sku);
        
        try {
          // Read all files in the product directory
          const files = fs.readdirSync(productPath)
            .filter(file => {
              const ext = path.extname(file).toLowerCase();
              return ['.jpg', '.jpeg', '.png', '.webp'].includes(ext);
            })
            .sort((a, b) => {
              // Sort by numeric value if possible, otherwise alphabetically
              const aNum = parseInt(a.split('.')[0]);
              const bNum = parseInt(b.split('.')[0]);
              if (!isNaN(aNum) && !isNaN(bNum)) {
                return aNum - bNum;
              }
              return a.localeCompare(b);
            });

          // Generate photo objects
          const photos = files.map((filename, index) => ({
            id: `${sku}-${index + 1}`,
            filename: filename,
            path: `/photos/products/${sku}/${filename}`,
            order: index + 1
          }));

          return {
            sku: sku,
            totalImages: photos.length,
            photos: photos
          };
        } catch (error) {
          console.error(`Error reading product directory ${sku}:`, error);
          return {
            sku: sku,
            totalImages: 0,
            photos: []
          };
        }
      })
    );

    // Filter out products with no photos
    const validProducts = products.filter(product => product.totalImages > 0);

    const response = {
      products: validProducts,
      pagination: {
        page,
        limit,
        total: filteredDirs.length,
        totalPages: Math.ceil(filteredDirs.length / limit),
        hasNext: endIndex < filteredDirs.length,
        hasPrev: page > 1
      }
    };

    console.log('API response:', {
      productsCount: validProducts.length,
      pagination: response.pagination
    });

    return NextResponse.json(response);

  } catch (error) {
    console.error('Error loading products:', error);
    return NextResponse.json(
      { error: 'Failed to load products' },
      { status: 500 }
    );
  }
}
