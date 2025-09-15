import { NextRequest, NextResponse } from 'next/server';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { lookup } from 'mime-types';

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    // Reconstruct the file path from the dynamic segments
    const filePath = params.path.join('/');
    
    // Base path to the images directory (mounted in container as /app/images)
    const baseImagePath = '/app/images';
    const fullPath = join(baseImagePath, filePath);
    
    // Security check: ensure the path is within the allowed directory
    if (!fullPath.startsWith(baseImagePath)) {
      return NextResponse.json(
        { error: 'Access denied: Path outside allowed directory' },
        { status: 403 }
      );
    }
    
    // Check if file exists
    if (!existsSync(fullPath)) {
      return NextResponse.json(
        { error: `Image not found: ${filePath}` },
        { status: 404 }
      );
    }
    
    // Read the file
    const fileBuffer = readFileSync(fullPath);
    
    // Determine MIME type
    const mimeType = lookup(fullPath) || 'application/octet-stream';
    
    // Return the image with appropriate headers
    return new NextResponse(fileBuffer, {
      status: 200,
      headers: {
        'Content-Type': mimeType,
        'Cache-Control': 'public, max-age=86400', // Cache for 1 day
        'Access-Control-Allow-Origin': '*', // Allow CORS for images
      },
    });
    
  } catch (error) {
    console.error('Error serving image:', error);
    return NextResponse.json(
      { error: 'Error serving image' },
      { status: 500 }
    );
  }
}