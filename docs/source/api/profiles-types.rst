Profile data types
==================

.. py:class:: sbgc32.ProfileParameters

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``params_3``
        - ``bytes`` (134 bytes)
        - ``PARAMS_3`` raw profile block.
      * - ``params_ext``
        - ``bytes`` (104 bytes)
        - ``PARAMS_EXT`` raw profile block.
      * - ``params_ext2``
        - ``bytes`` (151 bytes)
        - ``PARAMS_EXT2`` raw profile block.
      * - ``params_ext3``
        - ``bytes`` (221 bytes)
        - ``PARAMS_EXT3`` raw profile block.

Related enums: :class:`~sbgc32.ProfileId`, :class:`~sbgc32.ProfileSet`,
:class:`~sbgc32.ProfileSetAction`, and :class:`~sbgc32.ProfileWritingAction`.
