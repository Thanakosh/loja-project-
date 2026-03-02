module.exports = {
  packagerConfig: {
    asar: true,
  },
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'LojaProject',
        authors: 'Thanakosh',
        description: 'Sistema de Gerenciamento Comercial Inteligente',
      },
    },
    {
      name: '@electron-forge/maker-zip',
    },
  ],
};
