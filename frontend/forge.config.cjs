module.exports = {
  packagerConfig: {
    asar: true,
  },
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'LojaProject',
      },
    },
    {
      name: '@electron-forge/maker-zip',
    },
  ],
};
