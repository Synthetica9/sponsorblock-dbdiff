# `sponsorblock-dbdiff`: Privacy-friendly Sponsorblock API

This is a proof-of-concept API for Sponsorblock that utilises a compressed variant of the whole database instead of issuing requests for every individual video.

## Resource usage

The initial database download is about 5MB. After that, a client can request deltas for new data, these amount to the order of 50KB per day since the last update.

## API

- `/`: returns a simple "Hello world" message. Might be used for general information about server health in the future.
- `/latest`: Gets the hash digest of the latest database
- `/snapshots/{digest}`: Get a (compressed) database image from the server. Can 404 if the snapshot is not available (anymore).
- `/diff/{old}/{new}`: Get the difference of two databases. Returns a hash that can be requested using the `/snapshots` endpoint. The database returned in that case will have two tables: `added` and `removed`. `added` contains the entries that were added between `old` and `new`, `removed` contains the entries that were removed.

### Typical usage

The typical usecase for a client that hasn't interacted with the server before would be as follows:

1. Client uses the `/latest` endpoint to request the latest hash digest.
2. Client requests `/snapshots/{thatHash}` and saves the result (both the hash and the database).

When a client wants to update their internal database, they do the following:

1. Client uses the `/latest` endpoint to request the latest hash digest.
2. Client uses `/diff/{old}/{new}` to request the hash of the diff database.
3. Client uses `/snapshots/{diffHash}` to request the snapshot of the diff and use this to update their internal view.

If the client is offline for too long, it could be that the snapshot they were using is no longer available. In this case, they delete their old snapshot and proceed as if they have not interacted with the server before.

## (Potential) future work

_In order of priority_:

- Less round-trips in the protocol
- Perhaps a more compressed database format.
- A nicer way of shipping deltas to clients.
- Support for distributed multi-server setups.
