import path from 'path'
export default () => [
  {
    test: /\.(png|jpe?g|gif|svg)$/,
    loader: 'url-loader',
    options: {
      outputPath: 'img',
      name: '[name][hash:7].[ext]',
      fallback: 'file-loader',
      esModule: false
    },
    exclude: [/monitor-static\/svg-icons/]
  },
  {
    test: /\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/,
    use: [
      {
        loader: 'url-loader',
        options: {
          limit: 8192,
          outputPath: 'media',
          name: '[name][hash:7].[ext]',
          fallback: 'file-loader'
        }
      }
    ]
  },
  {
    test: /\.(woff2?|eot|ttf|otf)(\?.*)?$/,
    use: [
      {
        loader: 'url-loader',
        options: {
          limit: 8192,
          outputPath: 'fonts',
          name: '[name][hash:7].[ext]',
          fallback: 'file-loader',
          publicPath: '/fonts'
        }
      }
    ]
  },
  {
    test: /\.svg$/,
    use: [
      {
        loader: 'svg-sprite-loader',
        options: {
          symbolId: 'icon-[name]',
          extract: false
        }
      },
      {
        loader: 'svgo-loader',
        options: {
          externalConfig: path.resolve(__dirname, '../../../config/svgo-config.yml')
        }
      }
    ],
    include: [/monitor-static\/svg-icons/]
  }
]
