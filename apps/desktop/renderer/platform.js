/* Shared client boundary. Mobile shells can provide the same methods through a native bridge. */
window.pmgoPlatform = Object.freeze({
  request: (options) => window.pmgo.request(options),
  saveProviderKey: (value) => window.pmgo.saveProviderKey(value),
  hasProviderKey: () => window.pmgo.hasProviderKey(),
  dataDir: () => window.pmgo.dataDir(),
  kind: 'desktop',
});
