import { NextResponse } from 'next/server';
import { NextRequest } from 'next/server';

// Mock subject assets data
const mockAssets = {
  '1': { // Matemáticas
    icon_url: '🔢',
    color_primary: '#8B5CF6',
    color_secondary: '#A78BFA'
  },
  '2': { // Lectura Crítica
    icon_url: '📚',
    color_primary: '#3B82F6',
    color_secondary: '#60A5FA'
  },
  '3': { // Ciencias Naturales
    icon_url: '🔬',
    color_primary: '#10B981',
    color_secondary: '#34D399'
  },
  '4': { // Ciencias Sociales
    icon_url: '🌍',
    color_primary: '#F59E0B',
    color_secondary: '#FBBF24'
  },
  '5': { // Inglés
    icon_url: '🌐',
    color_primary: '#EF4444',
    color_secondary: '#F87171'
  }
};

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const subjectId = params.id;
    
    // Get assets for the subject
    const assets = mockAssets[subjectId as keyof typeof mockAssets] || {
      icon_url: '📖',
      color_primary: '#6B7280',
      color_secondary: '#9CA3AF'
    };

    // Add a small delay to simulate network request
    await new Promise(resolve => setTimeout(resolve, 200));

    return NextResponse.json(assets, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      }
    });
  } catch (error) {
    console.error('Error in subject assets API:', error);
    return NextResponse.json(
      { 
        error: 'Failed to load subject assets',
        message: 'Internal server error'
      },
      { status: 500 }
    );
  }
}