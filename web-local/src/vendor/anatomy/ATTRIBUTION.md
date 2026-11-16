# Human body model attribution and licenses

## Active external-body model

ASTHRAL bundles makehuman-external-body.glb, downloaded as male-base-mesh-base_male.glb from the [Innerscene model page](https://www.innerscene.com/tools/library/3d-parts/male-base-mesh-3d-person-rigged-a-pose-380e6d89). The provider identifies the model as an Innerscene adaptation of MakeHuman CC0 assets and publishes it under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

Courtesy attribution: Innerscene; adapted from MakeHuman CC0 assets.

At import the file was 4,498,248 bytes, SHA-256 86c7cdfa989924b45e2e5110c131a4a4e6251ceb4e71246be68e468f3a32ca86. The source describes a neutral adult male base mesh in A-pose, approximately 119 × 49 × 179 cm, with a smooth external surface and rig. ASTHRAL does not render the skeleton. Skin weights and explicitly mapped rig bones support body-region navigation; spatial landmarks distinguish selected torso and head surfaces.

The model is a generic male-morphology orientation aid. It is not patient-specific, clinically validated, or suitable for diagnostic localization. The displayed size and shape do not represent an astronaut.

## Retained legacy model

zanatomy-muscles.glb is retained in the source tree to preserve its provenance and existing contribution history, but is excluded from application build and offline bundles. It was redistributed unmodified from ArianArsenal/anatomy-explorer, commit 8375d6ce7fec36e677c0eda66cae829ba55a4717, file public/models/muscles.glb.

Required attribution for this retained asset:

> Z-Anatomy, the libre 3D atlas of anatomy, by Gauthier Kervyn and Marcin Zielinski, derived from BodyParts3D by the Database Center for Life Science (DBCLS). Muscular-system GLB converted for web distribution by ArianArsenal/anatomy-explorer.

The converted model layer is licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); the underlying BodyParts3D dataset is attributed under [CC BY-SA 2.1 Japan](https://creativecommons.org/licenses/by-sa/2.1/jp/). See the upstream [model license](https://github.com/Z-Anatomy/Models-of-human-anatomy/blob/master/License.txt) and [conversion project license notes](https://github.com/ArianArsenal/anatomy-explorer#credits--license).

Its recorded integrity is 4,003,932 bytes; SHA-256 f8399ba12dedb7cd88de199eddf7e3f8a3de8373a69228fb9da7ce1b7981ffd2.
