wrk.method = "POST"
wrk.body   = "name=test&content=hello"
wrk.headers["Content-Type"] = "application/x-www-form-urlencoded"
wrk.headers["Cookie"] = "user=admin"

cnt = 0
errs = 0

request = function ()
    body = "name=test&content=hello" .. tostring(cnt)
    cnt = cnt + 1
    -- io.write("req " .. body .. "\n")
    return wrk.format(nil, "/edit_page", nil, body)
end

response = function (status, headers, body)
    -- out = ""
    -- for k, v in pairs(headers) do
    --     out = out .. k .. " -> " .. v .. "\n"
    -- end
    -- io.write(out)
    if string.find(headers["location"], "failed") then
        errs = errs + 1
        io.write(string.format("error %d/%d\n", errs, cnt))
    end
end

done = function(summary, latency, requests)
    io.write(string.format("%d/%d failed\n", errs, summary.requests))
end
