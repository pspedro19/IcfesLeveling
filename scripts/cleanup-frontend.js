#!/usr/bin/env node

/**
 * Frontend Cleanup Script for Production
 * Removes console.log, alert(), and other debug statements
 */

const fs = require('fs');
const path = require('path');

const frontendDir = path.join(__dirname, '..', 'apps', 'frontend');
const backupDir = path.join(__dirname, '..', 'backup', 'frontend-cleanup-' + Date.now());

// File extensions to process
const extensions = ['.ts', '.tsx', '.js', '.jsx'];

// Patterns to remove/replace
const patterns = [
  {
    pattern: /console\.(log|error|warn|info|debug)\([^)]*\);?\s*\n?/g,
    replacement: '',
    description: 'console statements'
  },
  {
    pattern: /alert\s*\([^)]*\);?\s*\n?/g,
    replacement: '// TODO: Replace with proper error handling\n',
    description: 'alert() statements'
  },
  {
    pattern: /debugger;?\s*\n?/g,
    replacement: '',
    description: 'debugger statements'
  }
];

let processedFiles = 0;
let totalReplacements = 0;

function shouldProcessFile(filePath) {
  const ext = path.extname(filePath);
  return extensions.includes(ext) && !filePath.includes('node_modules') && !filePath.includes('.next');
}

function createBackup(filePath, content) {
  const relativePath = path.relative(frontendDir, filePath);
  const backupFilePath = path.join(backupDir, relativePath);
  const backupDirPath = path.dirname(backupFilePath);
  
  if (!fs.existsSync(backupDirPath)) {
    fs.mkdirSync(backupDirPath, { recursive: true });
  }
  
  fs.writeFileSync(backupFilePath, content);
}

function processFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    let newContent = content;
    let fileReplacements = 0;
    
    // Create backup before modifying
    createBackup(filePath, content);
    
    patterns.forEach(({ pattern, replacement, description }) => {
      const matches = newContent.match(pattern);
      if (matches) {
        newContent = newContent.replace(pattern, replacement);
        fileReplacements += matches.length;
        console.log(`  - Removed ${matches.length} ${description}`);
      }
    });
    
    if (fileReplacements > 0) {
      fs.writeFileSync(filePath, newContent);
      totalReplacements += fileReplacements;
      console.log(`✅ Processed: ${path.relative(frontendDir, filePath)} (${fileReplacements} changes)`);
    }
    
    processedFiles++;
  } catch (error) {
    console.error(`❌ Error processing ${filePath}:`, error.message);
  }
}

function walkDirectory(dir) {
  const items = fs.readdirSync(dir);
  
  items.forEach(item => {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
      walkDirectory(fullPath);
    } else if (stat.isFile() && shouldProcessFile(fullPath)) {
      processFile(fullPath);
    }
  });
}

function main() {
  console.log('🧹 Starting frontend cleanup for production...\n');
  
  // Create backup directory
  if (!fs.existsSync(backupDir)) {
    fs.mkdirSync(backupDir, { recursive: true });
  }
  
  console.log(`📦 Backup created at: ${backupDir}\n`);
  
  // Process all files
  walkDirectory(frontendDir);
  
  console.log('\n📊 Cleanup Summary:');
  console.log(`- Files processed: ${processedFiles}`);
  console.log(`- Total replacements: ${totalReplacements}`);
  console.log(`- Backup location: ${backupDir}`);
  
  if (totalReplacements > 0) {
    console.log('\n✅ Frontend cleanup completed successfully!');
    console.log('\n⚠️  Important:');
    console.log('1. Test the application thoroughly after cleanup');
    console.log('2. Review the changes and restore from backup if needed');
    console.log('3. Update error handling where alert() was replaced');
  } else {
    console.log('\n✅ No cleanup needed - frontend is already production ready!');
  }
}

main();