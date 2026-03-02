module.exports = {
  packagerConfig: {
    asar: true,
  },
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'loja_project',
      },
    },
    {
      name: '@electron-forge/maker-zip',
    },
  ],
};
