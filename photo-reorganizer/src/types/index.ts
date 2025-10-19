export interface Photo {
  id: string;
  filename: string;
  path: string;
  order: number;
}

export interface Product {
  sku: string;
  photos: Photo[];
  totalImages: number;
}

export interface RenameInstruction {
  [sku: string]: {
    [oldName: string]: string;
  };
}

export interface DragEndEvent {
  active: {
    id: string;
    data: {
      current: {
        sku: string;
        photoId: string;
      };
    };
  };
  over: {
    id: string;
    data: {
      current: {
        sku: string;
        photoId: string;
      };
    };
  } | null;
}
