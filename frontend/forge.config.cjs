module.exports = {
  packagerConfig: {
    asar: true,
  },
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'loja-project',
      },
    },
    {
      name: '@electron-forge/maker-zip',
    },
  ],
};
