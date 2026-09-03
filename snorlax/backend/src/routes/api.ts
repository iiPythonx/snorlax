// Copyright (c) 2026 iiPython

import { Elysia, t } from "elysia";
import type { SnorlaxDB } from "../database";

const paginationQuery = t.Object({
    limit: t.Optional(t.Numeric({ minimum: 1, maximum: 30, default: 20 })),
    page: t.Optional(t.Numeric({ minimum: 1, default: 1 }))
});

export const apiRoutes = new Elysia({ prefix: "/v1" })
    .get("/channels", ({ db, query }) => {
        const { items, total } = (db as SnorlaxDB).getChannels(query.limit, query.page);
        return {
            code: 200,
            data: { items, total }
        };
    }, { query: paginationQuery })


    .get("/channel/:channel_id", ({ db, params, set }) => {
        const channel = (db as SnorlaxDB).getChannel(params.channel_id)
        if (!channel) {
            set.status = 404;
            return { code: 404, data: { message: "The specified channel does not exist." } };
        }
        return { code: 200, data: channel };
    })

    .get("/videos", ({ db, query }) => {
        const { items, total } = (db as SnorlaxDB).getVideos({
            query: query.query,
            channelId: query.channel_id,
            limit: query.limit,
            page: query.page
        });

        return {
            code: 200,
            data: { items, total }
        };
    }, {
        query: t.Composite([
            paginationQuery,
            t.Object({
                channel_id: t.Optional(t.String()),
                query: t.Optional(t.String())
            })
        ])
    })

    .get("/video/:video_id", ({ db, params, set }) => {
        const video = (db as SnorlaxDB).getVideo(params.video_id);
        if (!video) {
            set.status = 404;
            return { code: 404, data: { message: "The specified video does not exist." } };
        }
        return { code: 200, data: video };
    });
