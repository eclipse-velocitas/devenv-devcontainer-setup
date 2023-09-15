# Vehicle Signal Interface Support

The "vehicle model lifecycle" / "vehicle signal interface support" component defines the process how the "code-level" Velocitas data model is generated from the signal catalogue referenced in the app's manifest.

It consists roughly of the these steps:
* Getting the required dependencies needed for generating the model (e.g. the model generator itself)
* Making the referenced signal catalogue locally available (for the generator)
* Generating the signal interface model in the required programming language
