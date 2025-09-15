import { NextRequest, NextResponse } from 'next/server';
import { existsSync, readdirSync } from 'fs';
import { join } from 'path';

export async function GET(request: NextRequest) {
  try {
    // Base path to the images directory
    const baseImagePath = '/root/IcfesLeveling/database/allquestions';
    
    const debug = {
      cwd: process.cwd(),
      baseImagePath,
      exists: existsSync(baseImagePath),
      contents: existsSync(baseImagePath) ? readdirSync(baseImagePath) : 'Directory does not exist'
    };
    
    return NextResponse.json(debug);
    
  } catch (error) {
    return NextResponse.json(
      { error: 'Debug error', details: error },
      { status: 500 }
    );
  }
}