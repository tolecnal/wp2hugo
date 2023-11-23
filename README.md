# wp2hugo

This Python module helps you convert a WordPress WXR file to MD files.

The MD files can then be used to start up a Hugo site, making this module an important first step if you want to convert your WordPress site to Hugo.

## Description

The module has two run modes: `create` and `stats`.

Run mode `create` will open your WXR XML file and create the required MD files.

Run mode `stats` will dump some quick statistics about the WXR XML file, including number of posts, number of pages, number of tags and number of categories.

## Installation

Install the module using pip.

```shell
pip3 install wp2hugo
```

## Usage

### Create

To create the MD files, use `create`.

`wp2hugo create <xmlfile> --outdir <directory> --lowercasetags`

Parameters:

- `<xmlfile>`
  - Path to the WXR XML file
  - Required: yes
- `--outdir <directory>`
  - Path to the output directory, will be created if not existing
  - Default: ./out
  - Required: no
- `--lowercasetags`
  - Whether or not to convert tags from WXR files to lowercase
  - Default: false
  - Required: no

### stats

To display statistics about the WXR file, use `stats`.

`wp2hugo stats <xmlfile>`

Parameters:

- `<xmlfile>`
  - Path to the WXR XML file
  - Required: yes

## Create export file

The WXR export can be created using one of two methods:

- export from the WordPress web dashboard
- export made from using the `WP CLI` tool

### Wordpress web dashboard

Follow these steps to create the export.

- Log in to your WordPress site
- Go to `Tools -> Export`
- Ensure that `All content` is selected
- Click the `Download Export File` button

![Export image](https://i.imgur.com/wutZhh4.png)

Your web browswer will now download the generated export file.

### WP CLI tool

Setting up and using the WP CLI tool is outside the scope of this README, but please consult the [documentation](https://developer.wordpress.org/cli/commands/export/).

It is fairly straightforward, and requires either console access to where the WordPress files are located, or access via SSH.

## Credits

This Python module is heavily based on the `wxr2md` [module](https://github.com/nikolasdion/wxr2md) by Dion Susanto. A huge thanks go out to him for his work.

## License

MIT

## Author

This module was created by [Jostein Elvaker Haande](https://tolecnal.net).
