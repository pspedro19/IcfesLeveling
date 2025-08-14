import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  // Handle API proxying
  if (request.nextUrl.pathname.startsWith('/api/v1/')) {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
    const apiPath = request.nextUrl.pathname.replace('/api/v1', '');
    const searchParams = request.nextUrl.searchParams.toString();
    const targetUrl = `${backendUrl}${apiPath}${searchParams ? `?${searchParams}` : ''}`;
    
    return NextResponse.rewrite(new URL(targetUrl));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/api/v1/:path*',
  ],
};