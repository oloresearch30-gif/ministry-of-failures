export default {
  name: 'indexCard',
  title: 'Index Card',
  type: 'document',
  fields: [
    { name: 'number', title: 'Number', type: 'string' },
    { name: 'titleSi', title: 'Title (Sinhala)', type: 'string' },
    { name: 'titleEn', title: 'Title (English)', type: 'string' },
    { name: 'body', title: 'Body', type: 'text', rows: 6 },
    { name: 'image', title: 'Main Image', type: 'image', options: { hotspot: true } },
    {
      name: 'videos',
      title: 'Videos',
      type: 'array',
      of: [
        {
          type: 'object',
          name: 'videoItem',
          title: 'Video',
          fields: [
            { name: 'title', title: 'Title', type: 'string' },
            {
              name: 'file',
              title: 'Video File',
              type: 'file',
              options: { accept: 'video/mp4,video/webm,video/quicktime,video/x-msvideo' },
            },
          ],
          preview: {
            select: { title: 'title', filename: 'file.asset.originalFilename' },
            prepare({ title, filename }) {
              return { title: title || filename || 'Untitled Video', subtitle: '🎬 Video' }
            },
          },
        },
      ],
    },
    {
      name: 'images',
      title: 'Gallery Images',
      type: 'array',
      of: [
        {
          type: 'object',
          name: 'imageItem',
          title: 'Image',
          fields: [
            { name: 'title', title: 'Title', type: 'string' },
            {
              name: 'image',
              title: 'Image',
              type: 'image',
              options: { hotspot: true },
            },
          ],
          preview: {
            select: { title: 'title', media: 'image' },
          },
        },
      ],
    },
    {
      name: 'documents',
      title: 'Documents',
      type: 'array',
      of: [
        {
          type: 'object',
          name: 'documentItem',
          title: 'Document',
          fields: [
            { name: 'title', title: 'Title', type: 'string' },
            {
              name: 'file',
              title: 'Document File (PDF)',
              type: 'file',
              options: { accept: 'application/pdf' },
            },
          ],
          preview: {
            select: { title: 'title', filename: 'file.asset.originalFilename' },
            prepare({ title, filename }) {
              return { title: title || filename || 'Untitled Document', subtitle: '📄 PDF' }
            },
          },
        },
      ],
    },
    { name: 'tags', title: 'Tags', type: 'string' },
    {
      name: 'tagType',
      title: 'Tag Color',
      type: 'string',
      options: {
        list: [
          { title: 'Red', value: 'red' },
          { title: 'Yellow', value: 'yellow' },
        ],
      },
    },
    {
      name: 'year',
      title: 'Year',
      type: 'string',
      options: {
        list: [
          { title: '2025', value: '2025' },
          { title: '2026', value: '2026' },
          { title: '2027', value: '2027' },
        ],
        layout: 'radio',
      },
      initialValue: '2025',
    },
    { name: 'active', title: 'Active', type: 'boolean', initialValue: true },
  ],
  orderings: [
    {
      title: 'Number',
      name: 'numberAsc',
      by: [{ field: 'number', direction: 'asc' }],
    },
  ],
}