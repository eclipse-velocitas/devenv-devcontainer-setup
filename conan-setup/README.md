# Conan Setup

This component sets up the Conan client to use multiple additional remotes, possibly with credentials.

## Configurability

### Additional remotes

The component will read `$VELOCITAS_WORKSPACE/.conanremotes` and add all remotes listed in the file prior to the default (Conan center).
The file needs to contain a JSON array of additional remotes with keys `id`, `url`, `user` and `token`.

E.g.
```json
[
    {
        "id": "custom-remote",
        "url": "https://my-custom-remote.com/artifactory",
        "user": "my-user",
        "token": "${{ CONAN_REMOTE_TOKEN }}"
    }
]
```

### Remote credentials

The component will read `$VELOCITAS_WORKSPACE/.credentials` which is a list of plaintext key=value pairs which are then substituted in the `.conanremotes` file. That way a general configuration can be kept in the remote configuration while user-specific credentials can be kept in a separate file.

```text
CONAN_REMOTE_TOKEN=abdefghijk
```
