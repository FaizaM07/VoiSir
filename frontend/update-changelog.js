const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

try {
  // Get the latest commit message and author
  const commitMessage = execSync('git log -1 --pretty=%B').toString().trim();
  const commitAuthor = execSync('git log -1 --pretty=%an').toString().trim();
  
  // Get the current date
  const date = new Date().toISOString().split('T')[0];
  
  // Format the changelog entry
  const changelogEntry = `\n\n${date} - ${commitAuthor}\n- ${commitMessage.replace(/\n/g, '\n  ')}`;
  
  // Define the path to the changelog file
  const changelogPath = path.join(__dirname, '../changelog.txt');
  
  // Append the new entry to the changelog file
  fs.appendFileSync(changelogPath, changelogEntry);
  
  console.log('Changelog updated successfully.');
} catch (error) {
  console.error('Failed to update changelog:', error);
  process.exit(1);
}
