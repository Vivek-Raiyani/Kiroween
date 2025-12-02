// PostCSS configuration for autoprefixer
// Automatically adds vendor prefixes for cross-browser compatibility

module.exports = {
  plugins: [
    require('autoprefixer')({
      // Target browsers from package.json browserslist
      // This ensures we only add necessary prefixes
      overrideBrowserslist: [
        'Chrome >= 90',
        'Firefox >= 88',
        'Safari >= 14',
        'Edge >= 90',
        'iOS >= 14',
        'Android >= 90'
      ],
      // Remove outdated prefixes
      remove: true,
      // Add prefixes for flexbox
      flexbox: 'no-2009',
      // Add prefixes for grid
      grid: 'autoplace'
    })
  ]
};
